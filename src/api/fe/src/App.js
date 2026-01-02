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
      setError("Please select a PDF file.");
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
        throw new Error("Search failed");
      }

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError("Error searching for similar documents.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Legal Document Similarity Search</h1>

      <div className="upload-box">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
        />
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Searching..." : "Upload & Search"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {results.length > 0 && (
        <div className="results">
          <h2>Similar Documents</h2>
          <ul>
            {results.map((r, idx) => (
              <li key={idx}>
                <div>
    <strong>{r.document}</strong>
    <span className="score">score: {r.score}</span>
  </div>

  <div className="actions">
    <a
      href={r.download_url}
      target="_blank"
      rel="noopener noreferrer"
    >
      Open
    </a>

    <a
      href={r.download_url}
      download
      style={{ marginLeft: "10px" }}
    >
      Download
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
