import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils.js";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-sans font-medium transition-colors cursor-pointer select-none touch-manipulation focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#4c6ee6] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-40",
  {
    variants: {
      variant: {
        /* near-black pill — primary action */
        primary:  "bg-c-primary text-white rounded-pill hover:bg-[#2a2a33] active:bg-[#0a0a0e]",
        /* white pill on dark surface */
        light:    "bg-white text-c-primary rounded-pill hover:bg-c-stone active:bg-c-hairline",
        /* outline pill */
        outline:  "border border-c-primary text-c-primary bg-transparent rounded-xl hover:bg-c-primary hover:text-white active:bg-[#2a2a33] active:text-white",
        /* text link — underlined, no background */
        ghost:    "text-c-ink underline underline-offset-2 bg-transparent hover:text-c-primary",
        /* danger */
        danger:   "bg-c-error text-white rounded-pill hover:opacity-90",
      },
      size: {
        sm:      "h-8 px-4 text-xs",
        default: "h-11 px-6 text-sm",
        lg:      "h-12 px-8 text-base",
        icon:    "h-9 w-9",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  }
);

export function Button({ className, variant, size, asChild = false, ...props }) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { buttonVariants };
