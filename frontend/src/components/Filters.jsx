export default function Filters({
  counties,
  selectedCounty,
  setSelectedCounty,
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      <button
        onClick={() => setSelectedCounty(null)}
        className="px-3 py-1 rounded-full bg-red-100 text-red-600 text-sm"
      >
        All
      </button>

      {counties.map((c) => (
        <button
          key={c}
          onClick={() => setSelectedCounty(c)}
          className={`px-3 py-1 rounded-full text-sm whitespace-nowrap ${
            selectedCounty === c
              ? "bg-blue-600 text-white"
              : "bg-gray-200"
          }`}
        >
          {c}
        </button>
      ))}
    </div>
  );
}