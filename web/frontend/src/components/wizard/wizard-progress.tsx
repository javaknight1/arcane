import { cn } from "@/lib/utils";
import { STEPS, type StepIndex } from "@/types/wizard";

interface WizardProgressProps {
  currentStep: StepIndex;
  onStepClick: (step: StepIndex) => void;
}

export function WizardProgress({ currentStep, onStepClick }: WizardProgressProps) {
  return (
    <nav className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <li key={index} className="flex items-center flex-1 last:flex-none">
              <button
                type="button"
                onClick={() => {
                  if (index < currentStep) {
                    onStepClick(index as StepIndex);
                  }
                }}
                disabled={index > currentStep}
                className={cn(
                  "flex items-center gap-2 text-sm font-medium transition-colors",
                  isCompleted && "text-primary cursor-pointer hover:underline",
                  isCurrent && "text-foreground",
                  !isCompleted && !isCurrent && "text-muted-foreground"
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold",
                    isCompleted && "border-primary bg-primary text-primary-foreground",
                    isCurrent && "border-primary text-primary",
                    !isCompleted && !isCurrent && "border-muted-foreground/30"
                  )}
                >
                  {isCompleted ? "\u2713" : index + 1}
                </span>
                <span className="hidden sm:inline">{step.label}</span>
              </button>
              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-0.5 flex-1",
                    isCompleted ? "bg-primary" : "bg-muted-foreground/20"
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
