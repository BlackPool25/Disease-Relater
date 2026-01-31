"""
Risk Calculator Service

Business logic for calculating disease risk scores based on:
- Population prevalence as base risk
- Comorbidity relationships with multiplicative odds ratios
- Disease-category-specific lifestyle factor adjustments
- Age-based risk multipliers

Agent 3: Calculation Engine
- Uses prevalence-based base risk (not odds ratios)
- Multiplicative comorbidity multipliers
- Category-specific lifestyle adjustments (metabolic, cardiovascular, respiratory)
- Age-adjusted risk multipliers
"""

import logging
import math
from typing import Dict, List, Literal, Any

from api.schemas.calculate import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskScore,
    UserPosition,
    PullVector,
)

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculate disease risk scores using prevalence and comorbidity data.

    Implements a four-stage risk calculation:
    1. Base risk from population prevalence (demographics-specific)
    2. Comorbidity multipliers (multiplicative odds ratios)
    3. Lifestyle adjustments (category-specific multipliers)
    4. Age-based risk adjustments

    Disease categories based on ICD-10 chapters:
    - E (Endocrine): Metabolic diseases
    - I (Circulatory): Cardiovascular diseases
    - J (Respiratory): Respiratory diseases
    """

    # Risk level thresholds
    RISK_VERY_HIGH = 0.75
    RISK_HIGH = 0.50
    RISK_MODERATE = 0.25

    # Age thresholds and multipliers
    AGE_ELDERLY = 65
    AGE_MIDDLE = 45
    AGE_YOUNG = 30

    # Age multipliers by category
    AGE_MULTIPLIERS = {
        "metabolic": {
            "elderly": 1.3,  # 65+
            "middle": 1.15,  # 45-64
            "young_adult": 1.0,  # 30-44
            "young": 0.8,  # <30 (protective)
        },
        "cardiovascular": {
            "elderly": 1.5,  # 65+ (high impact)
            "middle": 1.25,  # 45-64
            "young_adult": 1.0,  # 30-44
            "young": 0.7,  # <30 (protective)
        },
        "respiratory": {
            "elderly": 1.2,  # 65+
            "middle": 1.1,  # 45-64
            "young_adult": 1.0,  # 30-44
            "young": 0.9,  # <30 (slight protection)
        },
        "other": {
            "elderly": 1.15,
            "middle": 1.05,
            "young_adult": 1.0,
            "young": 0.95,
        },
    }

    # BMI thresholds
    BMI_OVERWEIGHT = 25.0
    BMI_OBESE = 30.0

    # Disease category mappings (ICD-10 chapter -> category)
    DISEASE_CATEGORIES = {
        "E": "metabolic",  # Endocrine, nutritional and metabolic diseases
        "I": "cardiovascular",  # Diseases of the circulatory system
        "J": "respiratory",  # Diseases of the respiratory system
    }

    # Lifestyle multipliers by disease category
    LIFESTYLE_MULTIPLIERS = {
        "metabolic": {
            "bmi_obese": 1.5,  # BMI >= 30
            "bmi_overweight": 1.2,  # BMI 25-30
        },
        "cardiovascular": {
            "smoking": 1.8,
            "exercise_low": 1.3,  # sedentary or light
            "exercise_high": 0.7,  # active (protective)
        },
        "respiratory": {
            "smoking": 1.6,
        },
    }

    def __init__(self, supabase_client):
        """Initialize with Supabase client for database queries.

        Args:
            supabase_client: Initialized Supabase async client
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)
        # Cache for disease names to avoid repeated queries
        self._disease_names_cache: Dict[str, str] = {}

    async def calculate_risks(
        self, request: RiskCalculationRequest
    ) -> RiskCalculationResponse:
        """Calculate risk scores for a user based on their conditions.

        Four-stage calculation pipeline:
        1. Get base risks from population prevalence for all diseases
        2. Apply comorbidity multipliers for user's existing conditions
        3. Apply disease-category-specific lifestyle factor adjustments
        4. Apply age-based risk multipliers
        5. Calculate user position as weighted average of 3D vectors

        Args:
            request: RiskCalculationRequest with user data and conditions

        Returns:
            RiskCalculationResponse with scores and position

        Raises:
            ValueError: If conditions are invalid or not found in database
        """
        # Step 1: Validate and fetch existing conditions
        conditions = await self._get_conditions(request.existing_conditions)
        if not conditions:
            raise ValueError("No valid conditions found for provided ICD codes")

        # Step 2: Get base risks from prevalence for all diseases
        # Also populates disease names cache
        base_risks = await self._calculate_base_risks_for_all(request)

        # Step 3: Apply comorbidity multipliers
        risks_with_comorbidity = await self._apply_comorbidity_multipliers(
            base_risks, request.existing_conditions
        )

        # Step 4: Apply lifestyle factor adjustments (includes age adjustments)
        final_risks, contributing_factors = await self._apply_lifestyle_factors(
            risks_with_comorbidity, request
        )

        # Step 5: Convert to RiskScore objects and get top results
        risk_scores = await self._convert_to_risk_scores(
            final_risks, contributing_factors, conditions, request.existing_conditions
        )

        # Step 6: Calculate user position
        user_position = self._calculate_position(conditions)

        # Step 7: Calculate pull vectors toward high-risk diseases
        pull_vectors = await self._calculate_pull_vectors(
            final_risks, user_position, threshold=0.3
        )

        return RiskCalculationResponse(
            risk_scores=risk_scores,
            user_position=user_position,
            pull_vectors=pull_vectors,
            total_conditions_analyzed=len(conditions),
            analysis_metadata={
                "conditions_processed": [c.get("icd_code") for c in conditions],
                "related_diseases_analyzed": len(final_risks),
                "gender": request.gender,
                "age": request.age,
            },
        )

    async def _get_conditions(self, icd_codes: List[str]) -> List[Dict[str, Any]]:
        """Fetch disease data for given ICD codes.

        Optimized to use a single batch query instead of per-code queries.

        Args:
            icd_codes: List of ICD-10 codes

        Returns:
            List of disease records with 3D coordinates and prevalence
        """
        conditions = []

        try:
            # Batch fetch all conditions in one query
            response = (
                await self.client.table("diseases")
                .select(
                    "id, icd_code, name_english, name_german, "
                    "chapter_code, prevalence_male, prevalence_female, "
                    "prevalence_total, vector_x, vector_y, vector_z"
                )
                .in_("icd_code", icd_codes)
                .execute()
            )

            if response.data:
                for disease in response.data:
                    conditions.append(disease)
                    # Cache the disease name
                    self._disease_names_cache[disease["icd_code"]] = disease.get(
                        "name_english", disease["icd_code"]
                    )

            # Log any codes that weren't found
            found_codes = {c["icd_code"] for c in conditions}
            missing_codes = set(icd_codes) - found_codes
            for code in missing_codes:
                self.logger.warning(f"Disease not found: {code}")

        except Exception as e:
            self.logger.error(f"Error fetching conditions: {e}")

        return conditions

    async def _get_disease_names(self, icd_codes: List[str]) -> Dict[str, str]:
        """Fetch disease names for a list of ICD codes.

        Uses cached values when available, queries database for missing ones.

        Args:
            icd_codes: List of ICD-10 codes

        Returns:
            Dictionary mapping icd_code -> name_english
        """
        result: Dict[str, str] = {}
        codes_to_fetch: List[str] = []

        # Check cache first
        for code in icd_codes:
            if code in self._disease_names_cache:
                result[code] = self._disease_names_cache[code]
            else:
                codes_to_fetch.append(code)

        # Batch fetch missing codes
        if codes_to_fetch:
            try:
                # Fetch in batches to avoid query limits
                batch_size = 100
                for i in range(0, len(codes_to_fetch), batch_size):
                    batch = codes_to_fetch[i : i + batch_size]
                    response = (
                        await self.client.table("diseases")
                        .select("icd_code, name_english")
                        .in_("icd_code", batch)
                        .execute()
                    )

                    if response.data:
                        for disease in response.data:
                            code = disease["icd_code"]
                            name = disease.get("name_english") or code
                            result[code] = name
                            self._disease_names_cache[code] = name

            except Exception as e:
                self.logger.error(f"Error fetching disease names: {e}")

        # Fill in any missing codes with the code itself
        for code in icd_codes:
            if code not in result:
                result[code] = code

        return result

    def _get_disease_category(self, icd_code: str) -> str:
        """Get disease category from ICD code chapter.

        Maps ICD-10 chapter codes to disease categories:
        - E -> metabolic (Endocrine/nutritional)
        - I -> cardiovascular (Circulatory)
        - J -> respiratory (Respiratory)
        - Others -> other

        Args:
            icd_code: ICD-10 code (e.g., "E11", "I10")

        Returns:
            Disease category string
        """
        if not icd_code or len(icd_code) < 1:
            return "other"

        chapter = icd_code[0].upper()
        return self.DISEASE_CATEGORIES.get(chapter, "other")

    def _get_age_group(self, age: int) -> str:
        """Classify age into group for risk adjustment.

        Args:
            age: User's age in years

        Returns:
            Age group string: elderly, middle, young_adult, or young
        """
        if age >= self.AGE_ELDERLY:
            return "elderly"
        elif age >= self.AGE_MIDDLE:
            return "middle"
        elif age >= self.AGE_YOUNG:
            return "young_adult"
        return "young"

    async def _calculate_base_risks_for_all(
        self, request: RiskCalculationRequest
    ) -> Dict[str, float]:
        """Calculate base risk scores from population prevalence for all diseases.

        Algorithm:
        base_risk[disease] = prevalence[disease][sex]

        Uses the diseases table which has aggregated prevalence data.
        Also populates the disease names cache.

        Args:
            request: User request with demographics

        Returns:
            Dictionary mapping disease_id -> base_risk (0.0 to 1.0)
        """
        base_risks: Dict[str, float] = {}

        # Determine prevalence field based on gender
        prevalence_field = (
            "prevalence_male" if request.gender == "male" else "prevalence_female"
        )

        try:
            # Fetch all diseases with their prevalence and names
            response = (
                await self.client.table("diseases")
                .select(f"icd_code, name_english, {prevalence_field}, prevalence_total")
                .execute()
            )

            if response.data:
                for disease in response.data:
                    disease_id = disease["icd_code"]
                    # Use gender-specific prevalence if available, otherwise total
                    prevalence = disease.get(prevalence_field) or disease.get(
                        "prevalence_total", 0.0
                    )
                    base_risks[disease_id] = float(prevalence) if prevalence else 0.0

                    # Cache disease name
                    name = disease.get("name_english") or disease_id
                    self._disease_names_cache[disease_id] = name

        except Exception as e:
            self.logger.error(f"Error fetching base risks: {e}")

        return base_risks

    async def _apply_comorbidity_multipliers(
        self, base_risks: Dict[str, float], existing_conditions: List[str]
    ) -> Dict[str, float]:
        """Apply comorbidity multipliers to base risks.

        Algorithm:
        For each condition in user's existing conditions:
            Get related diseases from disease_relationships table
            For each related disease:
                risk[disease] *= odds_ratio[condition, disease]

        This implements multiplicative comorbidity effects where having
        one disease increases the risk of related diseases proportionally
        to their odds ratio.

        Optimized to use batch queries instead of per-condition queries.

        Args:
            base_risks: Dictionary of base risks by disease_id
            existing_conditions: List of user's condition ICD codes

        Returns:
            Modified risks with comorbidity multipliers applied
        """
        modified_risks = base_risks.copy()

        try:
            # Batch fetch all disease IDs for existing conditions
            disease_response = (
                await self.client.table("diseases")
                .select("id, icd_code")
                .in_("icd_code", existing_conditions)
                .execute()
            )

            if not disease_response.data:
                return modified_risks

            # Create mapping of disease_id -> icd_code and collect IDs
            disease_ids = []
            id_to_code = {}
            for disease in disease_response.data:
                disease_id = disease["id"]
                disease_ids.append(disease_id)
                id_to_code[disease_id] = disease["icd_code"]

            if not disease_ids:
                return modified_risks

            # Build OR filter for all disease IDs
            # Supabase requires the IDs to be formatted in specific way
            or_filters = ",".join(
                [f"disease_1_id.eq.{did},disease_2_id.eq.{did}" for did in disease_ids]
            )

            # Batch fetch all relationships for all conditions
            response = (
                await self.client.table("disease_relationships")
                .select(
                    "disease_1_id, disease_2_id, odds_ratio, "
                    "disease_1: diseases!disease_1_id(icd_code), "
                    "disease_2: diseases!disease_2_id(icd_code)"
                )
                .or_(or_filters)
                .execute()
            )

            if response.data:
                disease_id_set = set(disease_ids)
                for rel in response.data:
                    d1_id = rel["disease_1_id"]
                    d2_id = rel["disease_2_id"]

                    # Determine which disease is the user's condition
                    # and which is the "other" related disease
                    if d1_id in disease_id_set:
                        other_disease = rel.get("disease_2", {})
                        other_code = other_disease.get("icd_code", "")
                    elif d2_id in disease_id_set:
                        other_disease = rel.get("disease_1", {})
                        other_code = other_disease.get("icd_code", "")
                    else:
                        continue

                    if other_code and other_code in modified_risks:
                        odds_ratio = rel.get("odds_ratio", 1.0)
                        if odds_ratio and odds_ratio > 0:
                            # Multiplicative application
                            modified_risks[other_code] *= odds_ratio

        except Exception as e:
            self.logger.error(f"Error applying comorbidity multipliers: {e}")

        return modified_risks

    async def _apply_lifestyle_factors(
        self, risks: Dict[str, float], request: RiskCalculationRequest
    ) -> tuple[Dict[str, float], Dict[str, List[str]]]:
        """Apply disease-category-specific lifestyle and age factor adjustments.

        Applies multiplicative adjustments for:
        - BMI (metabolic diseases)
        - Smoking (cardiovascular and respiratory)
        - Exercise level (cardiovascular)
        - Age (all categories, with category-specific multipliers)

        Args:
            risks: Dictionary of risk scores by disease_id
            request: User request with BMI, smoking status, exercise level, age

        Returns:
            Tuple of (adjusted_risks, contributing_factors)
        """
        adjusted_risks: Dict[str, float] = {}
        contributing_factors: Dict[str, List[str]] = {}

        # Get age group once
        age_group = self._get_age_group(request.age)

        for disease_id, base_risk in risks.items():
            category = self._get_disease_category(disease_id)
            multiplier = 1.0
            factors: List[str] = []

            # BMI adjustments for metabolic diseases
            if category == "metabolic":
                if request.bmi >= self.BMI_OBESE:
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["metabolic"]["bmi_obese"]
                    factors.append("High BMI (obese) - metabolic impact")
                elif request.bmi >= self.BMI_OVERWEIGHT:
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["metabolic"][
                        "bmi_overweight"
                    ]
                    factors.append("Elevated BMI (overweight) - metabolic impact")

            # Smoking adjustments
            if request.smoking:
                if category == "cardiovascular":
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["cardiovascular"][
                        "smoking"
                    ]
                    factors.append("Smoking - cardiovascular impact")
                elif category == "respiratory":
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["respiratory"]["smoking"]
                    factors.append("Smoking - respiratory impact")

            # Exercise adjustments for cardiovascular
            if category == "cardiovascular":
                if request.exercise_level in ["sedentary", "light"]:
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["cardiovascular"][
                        "exercise_low"
                    ]
                    factors.append("Low exercise level - cardiovascular impact")
                elif request.exercise_level == "active":
                    multiplier *= self.LIFESTYLE_MULTIPLIERS["cardiovascular"][
                        "exercise_high"
                    ]
                    factors.append("Active lifestyle - cardiovascular protective")

            # Age-based adjustments (category-specific)
            age_multipliers = self.AGE_MULTIPLIERS.get(
                category, self.AGE_MULTIPLIERS["other"]
            )
            age_mult = age_multipliers.get(age_group, 1.0)
            if age_mult != 1.0:
                multiplier *= age_mult
                if age_mult > 1.0:
                    factors.append(f"Age ({request.age}) - increased {category} risk")
                else:
                    factors.append(f"Age ({request.age}) - lower {category} risk")

            # Apply multiplier and cap at 1.0
            adjusted_risk = min(1.0, base_risk * multiplier)
            adjusted_risks[disease_id] = adjusted_risk

            # Store contributing factors for this disease
            contributing_factors[disease_id] = factors

        return adjusted_risks, contributing_factors

    async def _get_disease_coordinates(
        self, icd_codes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Batch fetch 3D coordinates for diseases.

        Retrieves vector_x, vector_y, vector_z coordinates from the database
        for use in pull vector calculations.

        Args:
            icd_codes: List of ICD-10 codes to fetch coordinates for

        Returns:
            Dictionary mapping icd_code -> {x, y, z, name} coordinates
        """
        coords: Dict[str, Dict[str, Any]] = {}

        if not icd_codes:
            return coords

        try:
            # Batch fetch coordinates
            response = (
                await self.client.table("diseases")
                .select("icd_code, name_english, vector_x, vector_y, vector_z")
                .in_("icd_code", icd_codes)
                .execute()
            )

            if response.data:
                for disease in response.data:
                    code = disease["icd_code"]
                    coords[code] = {
                        "x": disease.get("vector_x") or 0.0,
                        "y": disease.get("vector_y") or 0.0,
                        "z": disease.get("vector_z") or 0.0,
                        "name": disease.get("name_english") or code,
                    }

        except Exception as e:
            self.logger.error(f"Error fetching disease coordinates: {e}")

        return coords

    async def _calculate_pull_vectors(
        self,
        risks: Dict[str, float],
        user_position: UserPosition,
        threshold: float = 0.3,
    ) -> List[PullVector]:
        """Calculate pull vectors from user position toward high-risk diseases.

        For each disease with risk > threshold:
        1. Get disease 3D coordinates from database
        2. Calculate vector: (disease_pos - user_pos) * risk
        3. Compute magnitude: sqrt(x² + y² + z²)

        Args:
            risks: Dictionary mapping disease_id -> risk score
            user_position: User's current position in 3D space
            threshold: Minimum risk score to include (default 0.3)

        Returns:
            List of PullVector objects for high-risk diseases
        """
        pull_vectors: List[PullVector] = []

        # Filter to high-risk diseases only
        high_risk_codes = [code for code, risk in risks.items() if risk > threshold]

        if not high_risk_codes:
            return pull_vectors

        # Batch fetch coordinates for all high-risk diseases
        disease_coords = await self._get_disease_coordinates(high_risk_codes)

        for code in high_risk_codes:
            if code not in disease_coords:
                continue

            risk = risks[code]
            coords = disease_coords[code]

            # Calculate direction vector: disease_pos - user_pos
            dx = coords["x"] - user_position.x
            dy = coords["y"] - user_position.y
            dz = coords["z"] - user_position.z

            # Scale by risk score
            vector_x = dx * risk
            vector_y = dy * risk
            vector_z = dz * risk

            # Calculate magnitude: sqrt(x² + y² + z²)
            magnitude = math.sqrt(vector_x**2 + vector_y**2 + vector_z**2)

            pull_vectors.append(
                PullVector(
                    disease_id=code,
                    disease_name=str(coords["name"]),
                    risk=round(risk, 4),
                    vector_x=round(vector_x, 4),
                    vector_y=round(vector_y, 4),
                    vector_z=round(vector_z, 4),
                    magnitude=round(magnitude, 4),
                )
            )

        # Sort by magnitude descending (strongest pull first)
        pull_vectors.sort(key=lambda pv: pv.magnitude, reverse=True)

        return pull_vectors

    async def _convert_to_risk_scores(
        self,
        risks: Dict[str, float],
        contributing_factors: Dict[str, List[str]],
        conditions: List[Dict],
        existing_conditions: List[str],
    ) -> List[RiskScore]:
        """Convert risk dictionary to list of RiskScore objects.

        Fetches disease names from database, filters out user's existing
        conditions and sorts by risk score.

        Args:
            risks: Dictionary of disease_id -> risk
            contributing_factors: Dictionary of disease_id -> list of factor strings
            conditions: User's existing conditions (for relationship tracking)
            existing_conditions: List of user's ICD codes (to exclude from results)

        Returns:
            List of RiskScore objects, sorted by risk descending
        """
        risk_scores: List[RiskScore] = []
        existing_set = set(existing_conditions)

        # Filter to diseases we want to include (non-zero risk, not existing)
        filtered_codes = [
            code
            for code, risk in risks.items()
            if risk > 0 and code not in existing_set
        ]

        # Batch fetch disease names
        disease_names = await self._get_disease_names(filtered_codes)

        for disease_id in filtered_codes:
            risk = risks[disease_id]

            # Get contributing factors for this disease
            factors = contributing_factors.get(disease_id, [])
            factors_list: List[str] = (
                factors if factors else ["Population prevalence baseline"]
            )

            # Get actual disease name
            disease_name = disease_names.get(disease_id, disease_id)

            # Classify risk level
            level = self._classify_risk_level(risk)

            risk_scores.append(
                RiskScore(
                    disease_id=disease_id,
                    disease_name=disease_name,
                    risk=round(risk, 4),
                    level=level,
                    contributing_factors=factors_list,
                )
            )

        # Sort by risk descending and return top results
        risk_scores.sort(key=lambda x: x.risk, reverse=True)
        return risk_scores[:50]  # Return top 50 to avoid overwhelming response

    def _calculate_position(self, conditions: List[Dict]) -> UserPosition:
        """Calculate user's position in 3D disease space.

        Computes weighted average of condition coordinates using prevalence
        as weights. This places the user closer to their most prevalent
        conditions in the 3D visualization space.

        Args:
            conditions: List of user's conditions with 3D vectors.
                Each dict should have: vector_x, vector_y, vector_z, prevalence_total

        Returns:
            UserPosition with x, y, z coordinates (bounded to [-1, 1])
        """
        # Handle empty input - return origin
        if not conditions:
            logger.debug("No conditions provided, returning origin position")
            return UserPosition(x=0.0, y=0.0, z=0.0)

        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0
        weighted_z = 0.0
        missing_coords_count = 0
        zero_weight_count = 0

        for condition in conditions:
            icd_code = condition.get("icd_code", "unknown")

            # Get prevalence as weight, log if missing or zero
            raw_weight = condition.get("prevalence_total")
            if raw_weight is None or raw_weight == 0:
                zero_weight_count += 1
                logger.debug(
                    f"Missing or zero prevalence for {icd_code}, using default weight=1.0"
                )
            weight = raw_weight if raw_weight else 1.0

            # Get 3D coordinates with validation
            raw_x = condition.get("vector_x")
            raw_y = condition.get("vector_y")
            raw_z = condition.get("vector_z")

            # Log and handle missing coordinates
            if raw_x is None or raw_y is None or raw_z is None:
                missing_coords_count += 1
                logger.debug(
                    f"Missing 3D coordinates for {icd_code}: "
                    f"x={raw_x}, y={raw_y}, z={raw_z}"
                )

            # Default missing coords to 0.0
            x = raw_x if raw_x is not None else 0.0
            y = raw_y if raw_y is not None else 0.0
            z = raw_z if raw_z is not None else 0.0

            # Validate coordinate bounds [-1, 1] and clamp if out of range
            x = max(-1.0, min(1.0, x))
            y = max(-1.0, min(1.0, y))
            z = max(-1.0, min(1.0, z))

            weighted_x += x * weight
            weighted_y += y * weight
            weighted_z += z * weight
            total_weight += weight

        # Log summary if issues were found
        if missing_coords_count > 0:
            logger.warning(
                f"Position calculation: {missing_coords_count}/{len(conditions)} "
                "conditions had missing 3D coordinates"
            )
        if zero_weight_count > 0:
            logger.debug(
                f"Position calculation: {zero_weight_count}/{len(conditions)} "
                "conditions had zero/missing prevalence"
            )

        # Handle edge case: all weights are zero (shouldn't happen after defaults)
        if total_weight == 0:
            logger.warning("Total weight is zero after processing, returning origin")
            return UserPosition(x=0.0, y=0.0, z=0.0)

        # Calculate weighted average and clamp output to valid range
        result_x = max(-1.0, min(1.0, round(weighted_x / total_weight, 4)))
        result_y = max(-1.0, min(1.0, round(weighted_y / total_weight, 4)))
        result_z = max(-1.0, min(1.0, round(weighted_z / total_weight, 4)))

        return UserPosition(x=result_x, y=result_y, z=result_z)

    def _classify_risk_level(
        self, risk_score: float
    ) -> Literal["low", "moderate", "high", "very_high"]:
        """Classify risk score into level category.

        Args:
            risk_score: Risk value between 0.0 and 1.0

        Returns:
            Risk level string: low, moderate, high, or very_high
        """
        if risk_score >= self.RISK_VERY_HIGH:
            return "very_high"
        elif risk_score >= self.RISK_HIGH:
            return "high"
        elif risk_score >= self.RISK_MODERATE:
            return "moderate"
        return "low"
