import { Suspense } from "react";
import { SignInForm } from "@/components/auth/SignInForm";

// useSearchParams() (for the post-sign-in "?next=" redirect) requires a Suspense
// boundary for static prerendering — see https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout
export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInForm />
    </Suspense>
  );
}
