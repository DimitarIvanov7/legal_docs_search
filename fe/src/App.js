import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResults([]);
    setError("");
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Моля изберете PDF файл.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/search/pdf", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Търсенето се провали");
      }

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError("Грешка при търсенето.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Търсачка на подобни съдебни дела</h1>

      <div className="upload-box">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
        />
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Търсене..." : "Търсене"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {results.length > 0 && (
        <div className="results">
          <h2>Подобни документи</h2>
          <ul>
            {results.map((r, idx) => (
              <li key={idx}>
                <div>
                  <strong>{r.document} |</strong>
                  <span className="score">близост: {r.score}</span>
                </div>

                <div className="actions">
                  <a
                    href={r.download_url}
                    download
                    style={{ marginLeft: "10px" }}
                  >
                    Изтегли
                  </a>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
