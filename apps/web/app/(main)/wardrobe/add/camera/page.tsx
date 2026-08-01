import { Suspense } from "react";
import { AddItemCamera } from "@/components/wardrobe/AddItemCamera";

export default function AddItemCameraPage() {
  return (
    <Suspense fallback={null}>
      <AddItemCamera />
    </Suspense>
  );
}
