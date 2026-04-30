export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="max-w-xl w-full text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-3">
          Personal Research Agent
        </h1>
        <p className="text-lg text-gray-500 mb-8">
          Your topics. Briefed.
        </p>
        <div className="bg-white rounded-xl border border-gray-200 p-6 text-left text-sm text-gray-600 space-y-2">
          <p className="font-semibold text-gray-800">Phase 1 — static pipeline</p>
          <p>
            The backend API is running at{" "}
            <code className="bg-gray-100 px-1 rounded">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </code>
          </p>
          <p>
            Trigger a briefing via{" "}
            <code className="bg-gray-100 px-1 rounded">
              POST /briefings/run
            </code>{" "}
            or check{" "}
            <code className="bg-gray-100 px-1 rounded">
              GET /health
            </code>
          </p>
        </div>
      </div>
    </main>
  );
}
