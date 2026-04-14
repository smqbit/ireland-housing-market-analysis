export default function Card({ children }) {
  return (
    <div className="bg-white p-4 rounded-2xl shadow-sm">
      {children}
    </div>
  );
}