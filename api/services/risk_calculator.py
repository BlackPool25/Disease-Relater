"""
Risk Calculator Service

Business logic for calculating disease risk scores based on:
- Existing conditions and their comorbidity relationships
- Demographic factors (age, gender, BMI, smoking, exercise)
- Prevalence data stratified by sex and age
- 3D disease coordinates for user positioning
"""

import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

from api.schemas.calculate import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskScore,
    UserPosition,
)

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculate disease risk scores using comorbidity data.

    Uses odds ratios from disease relationships, demographic modifiers,
    and prevalence data to compute risk scores and user position.
    """

    # Risk level thresholds
    RISK_VERY_HIGH = 0.75
    RISK_HIGH = 0.50
    RISK_MODERATE = 0.25

    # Demographic modifier weights
    BMI_OVERWEIGHT = 25.0
    BMI_OBESE = 30.0
    AGE_ELDERLY = 65
    AGE_MIDDLE = 45

    def __init__(self, supabase_client):
        """Initialize with Supabase client for database queries.

        Args:
            supabase_client: Initialized Supabase async client
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)

    async def calculate_risks(
        self, request: RiskCalculationRequest
    ) -> RiskCalculationResponse:
        """Calculate risk scores for a user based on their conditions.

        Algorithm:
        1. Validate and fetch existing condition data
        2. Get related diseases with odds ratios from relationships table
        3. Calculate base risk scores from odds ratios
        4. Apply demographic modifiers
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

        # Step 2: Get related diseases with odds ratios
        related_diseases = await self._get_related_diseases(request.existing_conditions)

        # Step 3: Calculate base risk scores
        risk_scores = self._calculate_base_risks(related_diseases, conditions, request)

        # Step 4: Apply demographic modifiers
        risk_scores = self._apply_modifiers(risk_scores, request)

        # Step 5: Calculate user position
        user_position = self._calculate_position(conditions)

        return RiskCalculationResponse(
            risk_scores=risk_scores,
            user_position=user_position,
            total_conditions_analyzed=len(conditions),
            analysis_metadata={
                "conditions_processed": [c.get("icd_code") for c in conditions],
                "related_diseases_found": len(related_diseases),
                "gender": request.gender,
                "age": request.age,
            },
        )

    async def _get_conditions(self, icd_codes: List[str]) -> List[Dict[str, Any]]:
        """Fetch disease data for given ICD codes.

        Args:
            icd_codes: List of ICD-10 codes

        Returns:
            List of disease records with 3D coordinates and prevalence
        """
        conditions = []

        for code in icd_codes:
            try:
                # Query diseases table for condition data
                response = (
                    await self.client.table("diseases")
                    .select(
                        "id, icd_code, name_english, name_german, "
                        "chapter_code, prevalence_male, prevalence_female, prevalence_total, "
                        "vector_x, vector_y, vector_z"
                    )
                    .eq("icd_code", code)
                    .execute()
                )

                if response.data and len(response.data) > 0:
                    conditions.append(response.data[0])
                else:
                    self.logger.warning(f"Disease not found: {code}")
            except Exception as e:
                self.logger.error(f"Error fetching condition {code}: {e}")

        return conditions

    async def _get_related_diseases(self, icd_codes: List[str]) -> List[Dict[str, Any]]:
        """Get diseases related to existing conditions via comorbidity relationships.

        Uses bidirectional search on disease_relationships table to find
        all diseases connected to user's conditions, ordered by odds ratio.

        Args:
            icd_codes: List of user's existing condition ICD codes

        Returns:
            List of related diseases with odds ratios and relationship data
        """
        related = []
        seen_diseases = set(icd_codes)  # Track to avoid duplicates

        for code in icd_codes:
            try:
                # Get disease ID first
                disease_response = (
                    await self.client.table("diseases")
                    .select("id")
                    .eq("icd_code", code)
                    .execute()
                )

                if not disease_response.data:
                    continue

                disease_id = disease_response.data[0]["id"]

                # Query relationships where this disease is either source or target
                # Using or filter for bidirectional search
                response = (
                    await self.client.table("disease_relationships")
                    .select(
                        "disease_1_id, disease_2_id, odds_ratio, p_value, "
                        "patient_count_total, relationship_strength, "
                        "disease_1: diseases!disease_1_id(icd_code, name_english), "
                        "disease_2: diseases!disease_2_id(icd_code, name_english)"
                    )
                    .or_(f"disease_1_id.eq.{disease_id},disease_2_id.eq.{disease_id}")
                    .execute()
                )

                if response.data:
                    for rel in response.data:
                        # Determine which disease is the "other" one
                        if rel["disease_1_id"] == disease_id:
                            other_disease = rel.get("disease_2", {})
                            other_id = rel["disease_2_id"]
                        else:
                            other_disease = rel.get("disease_1", {})
                            other_id = rel["disease_1_id"]

                        other_code = other_disease.get("icd_code", "")

                        # Skip if already in user's conditions or seen
                        if other_code in seen_diseases:
                            continue

                        seen_diseases.add(other_code)

                        related.append(
                            {
                                "icd_code": other_code,
                                "disease_name": other_disease.get(
                                    "name_english", "Unknown"
                                ),
                                "odds_ratio": rel.get("odds_ratio", 1.0),
                                "p_value": rel.get("p_value"),
                                "patient_count": rel.get("patient_count_total", 0),
                                "relationship_strength": rel.get(
                                    "relationship_strength", "weak"
                                ),
                                "source_condition": code,
                            }
                        )

            except Exception as e:
                self.logger.error(f"Error fetching related diseases for {code}: {e}")

        # Sort by odds ratio descending
        related.sort(key=lambda x: x["odds_ratio"], reverse=True)
        return related

    def _calculate_base_risks(
        self,
        related_diseases: List[Dict],
        conditions: List[Dict],
        request: RiskCalculationRequest,
    ) -> List[RiskScore]:
        """Calculate base risk scores from odds ratios.

        Converts odds ratios to probability-like risk scores (0-1 range).
        Higher odds ratios = higher risk. Also considers prevalence data
        when available.

        Args:
            related_diseases: List of related diseases with odds ratios
            conditions: User's existing conditions
            request: Original request for demographic context

        Returns:
            List of RiskScore objects with base risk calculations
        """
        risk_scores = []

        # Get prevalence field based on gender
        prev_field = (
            "prevalence_male" if request.gender == "male" else "prevalence_female"
        )

        for disease in related_diseases:
            odds_ratio = disease.get("odds_ratio", 1.0)

            # Convert odds ratio to base risk using logistic-like function
            # This maps odds ratios to 0-1 range, with diminishing returns
            # OR=1 -> 0.0, OR=2 -> ~0.24, OR=5 -> ~0.44, OR=10 -> ~0.60, OR=50 -> ~0.90
            base_risk = odds_ratio / (odds_ratio + 3.0)

            contributing_factors = [
                f"Odds ratio: {odds_ratio:.2f} from {disease['source_condition']}",
            ]

            # Add relationship strength if significant
            strength = disease.get("relationship_strength", "weak")
            if strength in ["extreme", "very_strong", "strong"]:
                contributing_factors.append(
                    f"{strength.replace('_', ' ').title()} relationship"
                )

            risk_scores.append(
                RiskScore(
                    disease_id=disease["icd_code"],
                    disease_name=disease["disease_name"],
                    risk=round(base_risk, 4),
                    level=self._classify_risk_level(base_risk),
                    contributing_factors=contributing_factors,
                )
            )

        return risk_scores

    def _apply_modifiers(
        self,
        risk_scores: List[RiskScore],
        request: RiskCalculationRequest,
    ) -> List[RiskScore]:
        """Apply demographic modifiers to risk scores.

        Modifiers:
        - BMI: Overweight (+0.05), Obese (+0.10)
        - Smoking: +0.15 to all risks
        - Exercise: Sedentary (+0.05), Active (-0.05)
        - Age: Elderly (+0.10), Middle-aged (+0.05)

        Args:
            risk_scores: Current risk scores to modify
            request: User demographic data

        Returns:
            Modified risk scores with adjustments applied
        """
        modified_scores = []

        for score in risk_scores:
            modified_risk = score.risk
            new_factors = score.contributing_factors.copy()

            # BMI modifier
            if request.bmi >= self.BMI_OBESE:
                modified_risk += 0.10
                new_factors.append("High BMI (obese)")
            elif request.bmi >= self.BMI_OVERWEIGHT:
                modified_risk += 0.05
                new_factors.append("Elevated BMI (overweight)")

            # Smoking modifier
            if request.smoking:
                modified_risk += 0.15
                new_factors.append("Smoking status")

            # Exercise modifier
            if request.exercise_level == "sedentary":
                modified_risk += 0.05
                new_factors.append("Sedentary lifestyle")
            elif request.exercise_level == "active":
                modified_risk = max(0.0, modified_risk - 0.05)
                new_factors.append("Active lifestyle (protective)")

            # Age modifier
            if request.age >= self.AGE_ELDERLY:
                modified_risk += 0.10
                new_factors.append("Advanced age")
            elif request.age >= self.AGE_MIDDLE:
                modified_risk += 0.05
                new_factors.append("Middle age")

            # Cap at 1.0
            modified_risk = min(1.0, modified_risk)

            modified_scores.append(
                RiskScore(
                    disease_id=score.disease_id,
                    disease_name=score.disease_name,
                    risk=round(modified_risk, 4),
                    level=self._classify_risk_level(modified_risk),
                    contributing_factors=new_factors,
                )
            )

        return modified_scores

    def _calculate_position(self, conditions: List[Dict]) -> UserPosition:
        """Calculate user's position in 3D disease space.

        Computes weighted average of condition coordinates using prevalence
        as weights. This places the user closer to their most prevalent
        conditions in the 3D visualization space.

        Args:
            conditions: List of user's conditions with 3D vectors

        Returns:
            UserPosition with x, y, z coordinates
        """
        if not conditions:
            return UserPosition(x=0.0, y=0.0, z=0.0)

        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0
        weighted_z = 0.0

        for condition in conditions:
            # Use prevalence_total as weight, default to 1.0 if not available
            weight = condition.get("prevalence_total") or 1.0

            # Get 3D coordinates, default to 0 if not available
            x = condition.get("vector_x") or 0.0
            y = condition.get("vector_y") or 0.0
            z = condition.get("vector_z") or 0.0

            weighted_x += x * weight
            weighted_y += y * weight
            weighted_z += z * weight
            total_weight += weight

        if total_weight == 0:
            return UserPosition(x=0.0, y=0.0, z=0.0)

        return UserPosition(
            x=round(weighted_x / total_weight, 4),
            y=round(weighted_y / total_weight, 4),
            z=round(weighted_z / total_weight, 4),
        )

    def _classify_risk_level(self, risk_score: float) -> str:
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
