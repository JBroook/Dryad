import type { JSX } from "react";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "calendar-date": React.HTMLAttributes<HTMLElement> & {
        value?: string;
      };
      "calendar-month": React.HTMLAttributes<HTMLElement>;
    }
  }
}