"use client";

import { useReducer, useCallback } from "react";
import type {
  WizardState,
  WizardAction,
  WizardFormData,
  StepIndex,
} from "@/types/wizard";
import { INITIAL_FORM_DATA } from "@/types/wizard";

const initialState: WizardState = {
  currentStep: 0,
  formData: INITIAL_FORM_DATA,
  errors: {},
};

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, currentStep: action.step, errors: {} };
    case "UPDATE_FIELD":
      return {
        ...state,
        formData: { ...state.formData, [action.field]: action.value },
      };
    case "SET_ERRORS":
      return { ...state, errors: action.errors };
    case "CLEAR_ERRORS":
      return { ...state, errors: {} };
  }
}

export function validateStep(
  step: StepIndex,
  data: WizardFormData
): Record<string, string> {
  const errors: Record<string, string> = {};

  switch (step) {
    case 0:
      if (!data.project_name.trim())
        errors.project_name = "Project name is required";
      if (!data.vision.trim()) errors.vision = "Vision is required";
      if (!data.problem_statement.trim())
        errors.problem_statement = "Problem statement is required";
      if (data.target_users.length === 0)
        errors.target_users = "Add at least one target user";
      break;
    case 1:
      if (!data.timeline) errors.timeline = "Select a timeline";
      if (!data.developer_experience)
        errors.developer_experience = "Select experience level";
      if (!data.budget_constraints)
        errors.budget_constraints = "Select budget constraints";
      if (data.team_size < 1 || data.team_size > 100)
        errors.team_size = "Team size must be 1-100";
      break;
    case 2:
      // No required fields
      break;
    case 3:
      if (data.must_have_features.length === 0)
        errors.must_have_features = "Add at least one must-have feature";
      break;
    case 4:
      // Review step - no validation
      break;
  }

  return errors;
}

export function useWizard() {
  const [state, dispatch] = useReducer(wizardReducer, initialState);

  const updateField = useCallback(
    <K extends keyof WizardFormData>(field: K, value: WizardFormData[K]) => {
      dispatch({ type: "UPDATE_FIELD", field, value });
    },
    []
  );

  const goToStep = useCallback((step: StepIndex) => {
    dispatch({ type: "SET_STEP", step });
  }, []);

  const nextStep = useCallback((): boolean => {
    const errors = validateStep(state.currentStep, state.formData);
    if (Object.keys(errors).length > 0) {
      dispatch({ type: "SET_ERRORS", errors });
      return false;
    }
    if (state.currentStep < 4) {
      dispatch({ type: "SET_STEP", step: (state.currentStep + 1) as StepIndex });
    }
    return true;
  }, [state.currentStep, state.formData]);

  const prevStep = useCallback(() => {
    if (state.currentStep > 0) {
      dispatch({ type: "SET_STEP", step: (state.currentStep - 1) as StepIndex });
    }
  }, [state.currentStep]);

  return {
    state,
    updateField,
    goToStep,
    nextStep,
    prevStep,
  };
}
