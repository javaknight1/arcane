"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Pencil, Plus, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EditableFieldProps {
  value: string;
  onSave: (value: string) => void;
  multiline?: boolean;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  inputType?: "text" | "number";
}

export function EditableField({
  value,
  onSave,
  multiline = false,
  className,
  placeholder = "Click to edit...",
  disabled = false,
  inputType = "text",
}: EditableFieldProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      if (inputRef.current instanceof HTMLTextAreaElement) {
        inputRef.current.selectionStart = inputRef.current.value.length;
      }
    }
  }, [editing]);

  const save = useCallback(() => {
    setEditing(false);
    const trimmed = draft.trim();
    if (trimmed !== value) {
      onSave(trimmed);
    }
  }, [draft, value, onSave]);

  const cancel = useCallback(() => {
    setDraft(value);
    setEditing(false);
  }, [value]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        cancel();
      } else if (e.key === "Enter" && !multiline) {
        e.preventDefault();
        save();
      }
    },
    [cancel, save, multiline]
  );

  if (disabled) {
    return (
      <p className={cn("text-sm", className)}>
        {value || <span className="text-muted-foreground italic">{placeholder}</span>}
      </p>
    );
  }

  if (editing) {
    if (multiline) {
      return (
        <Textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={save}
          onKeyDown={handleKeyDown}
          className={cn("text-sm min-h-[60px]", className)}
          placeholder={placeholder}
        />
      );
    }
    return (
      <Input
        ref={inputRef as React.RefObject<HTMLInputElement>}
        type={inputType}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={save}
        onKeyDown={handleKeyDown}
        className={cn("text-sm h-8", className)}
        placeholder={placeholder}
      />
    );
  }

  return (
    <div
      className={cn(
        "group/edit flex items-start gap-1.5 cursor-pointer rounded-md px-1.5 py-1 -mx-1.5 -my-1 hover:bg-accent/50 transition-colors",
        className
      )}
      onClick={() => setEditing(true)}
    >
      <span className={cn("text-sm flex-1", !value && "text-muted-foreground italic")}>
        {multiline ? (
          <span className="whitespace-pre-wrap">{value || placeholder}</span>
        ) : (
          value || placeholder
        )}
      </span>
      <Pencil className="h-3 w-3 shrink-0 mt-0.5 opacity-0 group-hover/edit:opacity-50 transition-opacity" />
    </div>
  );
}

interface EditableListProps {
  items: string[];
  onSave: (items: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function EditableList({
  items,
  onSave,
  placeholder = "Add item...",
  disabled = false,
}: EditableListProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [adding, setAdding] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if ((editingIndex !== null || adding) && inputRef.current) {
      inputRef.current.focus();
    }
  }, [editingIndex, adding]);

  const saveEdit = useCallback(
    (index: number) => {
      const trimmed = draft.trim();
      if (trimmed && trimmed !== items[index]) {
        const updated = [...items];
        updated[index] = trimmed;
        onSave(updated);
      }
      setEditingIndex(null);
      setDraft("");
    },
    [draft, items, onSave]
  );

  const saveNew = useCallback(() => {
    const trimmed = draft.trim();
    if (trimmed) {
      onSave([...items, trimmed]);
    }
    setAdding(false);
    setDraft("");
  }, [draft, items, onSave]);

  const remove = useCallback(
    (index: number) => {
      onSave(items.filter((_, i) => i !== index));
    },
    [items, onSave]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, action: () => void) => {
      if (e.key === "Escape") {
        setEditingIndex(null);
        setAdding(false);
        setDraft("");
      } else if (e.key === "Enter") {
        e.preventDefault();
        action();
      }
    },
    []
  );

  return (
    <div className="space-y-1">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1 group/listitem">
          {editingIndex === i ? (
            <Input
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={() => saveEdit(i)}
              onKeyDown={(e) => handleKeyDown(e, () => saveEdit(i))}
              className="text-sm h-7 flex-1"
            />
          ) : (
            <>
              <span
                className="text-sm flex-1 cursor-pointer rounded px-1.5 py-0.5 -mx-1.5 hover:bg-accent/50 transition-colors"
                onClick={() => {
                  if (!disabled) {
                    setEditingIndex(i);
                    setDraft(item);
                  }
                }}
              >
                {item}
              </span>
              {!disabled && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 opacity-0 group-hover/listitem:opacity-100 transition-opacity shrink-0"
                  onClick={() => remove(i)}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </>
          )}
        </div>
      ))}
      {adding ? (
        <Input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={saveNew}
          onKeyDown={(e) => handleKeyDown(e, saveNew)}
          placeholder={placeholder}
          className="text-sm h-7"
        />
      ) : (
        !disabled && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs text-muted-foreground"
            onClick={() => {
              setAdding(true);
              setDraft("");
            }}
          >
            <Plus className="h-3 w-3 mr-1" />
            Add
          </Button>
        )
      )}
    </div>
  );
}
