import { useState } from "react";
import { BookOpen, Heart, MessageCircle, Sparkles } from "lucide-react";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import { useRAG } from "../hooks/useRAG";
import MemoryList from "../components/rag/MemoryList";
import RagContextPreview from "../components/rag/RagContextPreview";
import DocumentUploader from "../components/rag/DocumentUploader";
import DocumentList from "../components/rag/DocumentList";
import "../styles/user-rag.css";

type Tab = "preferences" | "guidance" | "documents";

const TABS: { key: Tab; label: string; description: string; Icon: React.ElementType }[] = [
  { key: "preferences", label: "Your preferences", description: "What matters to you", Icon: Heart },
  { key: "guidance", label: "Planning guidance", description: "How your choices help", Icon: MessageCircle },
  { key: "documents", label: "Useful documents", description: "Information for your plans", Icon: BookOpen },
];

export default function RagPage() {
  const navigate = useNavigate();
  const { userId } = useUser();
  const { isLoading: ragLoading, onIngestDocument } = useRAG();
  const [tab, setTab] = useState<Tab>("preferences");

  return (
    <div className="product-page resources-page">
      <header className="product-header">
        <div className="product-header-inner resources-header-inner">
          <span className="product-header-icon resources-header-icon"><Sparkles size={19} aria-hidden="true" /></span>
          <div>
            <h1>Your planning companion</h1>
            <p>Keep the information that helps make your plans work better for you.</p>
          </div>
          <button type="button" className="resources-header-link" onClick={() => navigate("/user")}>
            <ArrowLeft size={14} aria-hidden="true" />
            My profile
          </button>
        </div>
      </header>

      <main className="product-main resources-main">
        <section className="rag-hero">
          <div className="rag-hero-copy">
            <span className="rag-hero-label"><Sparkles size={14} aria-hidden="true" /> Make it yours</span>
            <h2>Plans that remember what matters to you.</h2>
            <p>Save your preferences and guidance once. They can then help shape the planning experience every time.</p>
          </div>
          <div className="rag-hero-art" aria-hidden="true">
            <span /><span /><span />
          </div>
        </section>

        <nav className="rag-choice-list" aria-label="Planning companion sections">
          {TABS.map(({ key, label, description, Icon }) => (
            <button key={key} type="button" onClick={() => setTab(key)} className={`rag-choice ${tab === key ? "is-active" : ""}`}>
              <span className="rag-choice-icon"><Icon size={17} aria-hidden="true" /></span>
              <span className="rag-choice-copy"><strong>{label}</strong><small>{description}</small></span>
              <span className="rag-choice-arrow" aria-hidden="true">→</span>
            </button>
          ))}
        </nav>

        <section className="rag-content-panel">
          {tab === "preferences" && <MemoryList userId={userId} />}
          {tab === "guidance" && <RagContextPreview userId={userId} />}
          {tab === "documents" && <div className="resource-document-stack"><DocumentUploader onIngest={onIngestDocument} isLoading={ragLoading} /><DocumentList /></div>}
        </section>

        <p className="resources-footnote">Your choices are used only to make your planning workspace more helpful.</p>
      </main>
    </div>
  );
}
