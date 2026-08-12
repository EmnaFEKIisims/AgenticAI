import { useState } from "react";
import { mergeConstraints, validateConstraints } from "../utils/constraintHelpers.js";

export default function useConstraintAgent(initial = { pedagogicalText: "", userText: "" }) {
  const [value, setValue] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [merged, setMerged] = useState(null);
  const [validation, setValidation] = useState(null);
  const [error, setError] = useState(null);

  const setValues = (patch) => setValue((v) => ({ ...v, ...patch }));

  const reset = () => {
    setValue(initial);
    setMerged(null);
    setValidation(null);
    setError(null);
    setLoading(false);
  };

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const mergedResult = mergeConstraints([], value.pedagogicalText, value.userText);
      setMerged(mergedResult);
      const validationResult = validateConstraints(mergedResult);
      setValidation(validationResult);
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return {
    value,
    setValues,
    generate,
    reset,
    loading,
    merged,
    validation,
    error,
  };
}
