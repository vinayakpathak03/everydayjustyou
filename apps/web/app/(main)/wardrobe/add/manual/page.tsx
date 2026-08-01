import { Suspense } from "react";
import { AddItemManual } from "@/components/wardrobe/AddItemManual";

export default function AddItemManualPage() {
  return (
    <Suspense fallback={null}>
      <AddItemManual />
    </Suspense>
  );
}
