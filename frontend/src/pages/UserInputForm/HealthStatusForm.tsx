/**
 * HealthStatusForm Component
 * 
 * Step 2 of the risk calculator - selects existing health conditions.
 * Features searchable condition categories with ICD-10 codes.
 */
import { useState, useMemo } from 'react';
import type { HealthStatusData } from '../../hooks/useFormState';
import { COMMON_CONDITIONS } from '../../api/diseases';
import './UserInputForm.css';

interface HealthStatusFormProps {
  data: HealthStatusData;
  onChange: (data: Partial<HealthStatusData>) => void;
}

/**
 * Category display names and icons
 */
const CATEGORY_META: Record<string, { name: string; icon: string }> = {
  cardiovascular: { name: 'Cardiovascular', icon: '❤️' },
  metabolic: { name: 'Metabolic & Endocrine', icon: '⚗️' },
  respiratory: { name: 'Respiratory', icon: '🫁' },
  mental: { name: 'Mental Health', icon: '🧠' },
  musculoskeletal: { name: 'Musculoskeletal', icon: '🦴' },
};

export function HealthStatusForm({ data, onChange }: HealthStatusFormProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('cardiovascular');

  // Toggle condition selection
  const toggleCondition = (code: string) => {
    const current = data.existingConditions;
    const updated = current.includes(code)
      ? current.filter((c) => c !== code)
      : [...current, code];
    onChange({ existingConditions: updated });
  };

  // Type for filtered conditions (more flexible than the readonly const type)
  type ConditionItem = { readonly code: string; readonly label: string };
  type FilteredConditions = Record<string, readonly ConditionItem[]>;

  // Filter conditions by search term
  const filteredConditions = useMemo((): FilteredConditions => {
    if (!searchTerm.trim()) return COMMON_CONDITIONS;

    const term = searchTerm.toLowerCase();
    const filtered: FilteredConditions = {};

    for (const [category, conditions] of Object.entries(COMMON_CONDITIONS)) {
      const matches = conditions.filter(
        (c) =>
          c.label.toLowerCase().includes(term) ||
          c.code.toLowerCase().includes(term)
      );
      if (matches.length > 0) {
        filtered[category] = matches;
      }
    }

    return filtered;
  }, [searchTerm]);

  const selectedCount = data.existingConditions.length;

  return (
    <div className="form-section">
      <div className="form-section-header">
        <span className="step-badge">02</span>
        <div>
          <h2 className="form-section-title">Health Status</h2>
          <p className="form-section-subtitle">
            Select your existing conditions 
            <span className="selection-count">
              {selectedCount > 0 && ` • ${selectedCount} selected`}
            </span>
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search conditions by name or ICD code..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        {searchTerm && (
          <button
            className="search-clear"
            onClick={() => setSearchTerm('')}
            aria-label="Clear search"
          >
            ×
          </button>
        )}
      </div>

      {/* Selected conditions pills */}
      {selectedCount > 0 && (
        <div className="selected-conditions">
          {data.existingConditions.map((code) => {
            // Find condition for display (currently only showing code)
            const _condition = Object.values(COMMON_CONDITIONS)
              .flat()
              .find((c) => c.code === code);
            void _condition; // Suppress unused variable warning
            return (
              <button
                key={code}
                className="condition-pill"
                onClick={() => toggleCondition(code)}
                title="Click to remove"
              >
                <span className="pill-code">{code}</span>
                <span className="pill-remove">×</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Condition categories */}
      <div className="condition-categories">
        {Object.entries(filteredConditions).map(([category, conditions]) => {
          const meta = CATEGORY_META[category] || { name: category, icon: '🏥' };
          const isExpanded = expandedCategory === category;
          const selectedInCategory = conditions.filter((c) =>
            data.existingConditions.includes(c.code)
          ).length;

          return (
            <div key={category} className={`category-card ${isExpanded ? 'expanded' : ''}`}>
              <button
                className="category-header"
                onClick={() => setExpandedCategory(isExpanded ? null : category)}
              >
                <span className="category-icon">{meta.icon}</span>
                <span className="category-name">{meta.name}</span>
                {selectedInCategory > 0 && (
                  <span className="category-count">{selectedInCategory}</span>
                )}
                <span className={`category-chevron ${isExpanded ? 'open' : ''}`}>▼</span>
              </button>

              {isExpanded && (
                <div className="category-conditions">
                  {conditions.map((condition) => {
                    const isSelected = data.existingConditions.includes(condition.code);
                    return (
                      <label
                        key={condition.code}
                        className={`condition-item ${isSelected ? 'selected' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleCondition(condition.code)}
                        />
                        <span className="condition-checkbox">
                          {isSelected && '✓'}
                        </span>
                        <span className="condition-label">{condition.label}</span>
                        <span className="condition-code">{condition.code}</span>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {Object.keys(filteredConditions).length === 0 && (
        <div className="no-results">
          No conditions match "{searchTerm}"
        </div>
      )}
    </div>
  );
}
