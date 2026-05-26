import { useRef } from "react";
import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import HowItWorks from "./components/HowItWorks.jsx";
import Tool from "./components/Tool.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  const toolRef = useRef(null);

  const scrollToTool = () => {
    toolRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <Navbar onTryClick={scrollToTool} />
      <main>
        <Hero onTryClick={scrollToTool} />
        <HowItWorks />
        <div ref={toolRef}>
          <Tool />
        </div>
      </main>
      <Footer />
    </>
  );
}
