"use client";

export default function EditorTexto({ onSalvar, valor }) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
      <textarea
        value={valor || ""}
        onChange={(e) => onSalvar(e.target.value)}
        className="w-full p-4 min-h-[300px] focus:outline-none resize-none"
        placeholder="Insira observações clínicas privadas aqui..."
      />
    </div>
  );
}
