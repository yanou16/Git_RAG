import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils.js";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:  "bg-slate-100 text-slate-700 text-xs px-2.5 py-0.5",
        primary:  "bg-blue-50 text-blue-700 border border-blue-200 text-xs px-2.5 py-0.5",
        success:  "bg-green-50 text-green-700 border border-green-200 text-xs px-2.5 py-0.5",
        warning:  "bg-amber-50 text-amber-700 border border-amber-200 text-xs px-2.5 py-0.5",
        mono:     "bg-slate-100 text-slate-600 font-mono text-[11px] px-2 py-0.5",
        outline:  "border border-slate-300 text-slate-600 bg-white text-xs px-2.5 py-0.5",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
