import React from "react";

declare module "lucide-react" {
  export type IconProps = React.SVGProps<SVGSVGElement> & {
    size?: number | string;
    color?: string;
    strokeWidth?: number | string;
    className?: string;
  };

  export type LucideIcon = React.ComponentType<IconProps>;

  export const Activity: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const AlertTriangle: LucideIcon;
  export const ArrowRight: LucideIcon;
  export const Award: LucideIcon;
  export const BarChart2: LucideIcon;
  export const BarChart3: LucideIcon;
  export const BookOpen: LucideIcon;
  export const BrainCircuit: LucideIcon;
  export const Check: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const CheckCircle2: LucideIcon;
  export const Clock: LucideIcon;
  export const Compass: LucideIcon;
  export const Cpu: LucideIcon;
  export const Database: LucideIcon;
  export const Droplets: LucideIcon;
  export const ExternalLink: LucideIcon;
  export const Fan: LucideIcon;
  export const FileText: LucideIcon;
  export const Filter: LucideIcon;
  export const Flame: LucideIcon;
  export const Gauge: LucideIcon;
  export const Globe: LucideIcon;
  export const History: LucideIcon;
  export const Home: LucideIcon;
  export const Info: LucideIcon;
  export const Layers: LucideIcon;
  export const Lightbulb: LucideIcon;
  export const LineChart: LucideIcon;
  export const Menu: LucideIcon;
  export const Pause: LucideIcon;
  export const Play: LucideIcon;
  export const PlaySquare: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const RotateCcw: LucideIcon;
  export const Save: LucideIcon;
  export const ShieldAlert: LucideIcon;
  export const ShieldCheck: LucideIcon;
  export const Sliders: LucideIcon;
  export const StepForward: LucideIcon;
  export const Sun: LucideIcon;
  export const Target: LucideIcon;
  export const Terminal: LucideIcon;
  export const Thermometer: LucideIcon;
  export const Users: LucideIcon;
  export const UserX: LucideIcon;
  export const Wind: LucideIcon;
  export const X: LucideIcon;
  export const XCircle: LucideIcon;
  export const Zap: LucideIcon;

  export const icons: Record<string, LucideIcon>;
  const Lucide: Record<string, LucideIcon>;
  export default Lucide;
}
