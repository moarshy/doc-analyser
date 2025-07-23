import { Hero, Features, HowItWorks, CTA } from '@/components/landing';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Hero />
      <Features />
      <HowItWorks />
      <CTA />
    </div>
  );
}
