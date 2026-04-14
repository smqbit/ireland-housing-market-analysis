import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import County from "./pages/County";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/county/:name" element={<County />} />
      </Routes>
    </BrowserRouter>
  );
}