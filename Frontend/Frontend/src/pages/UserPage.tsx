import { ArrowRight, CalendarDays, Sparkles, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import UserProfile from "../components/user/UserProfile";
import "../styles/user-rag.css";

export default function UserPage() {
  const navigate = useNavigate();

  return (
    <div className="product-page user-page">
      <header className="product-header">
        <div className="product-header-inner user-header-inner">
          <span className="product-header-icon user-header-icon"><UserRound size={19} aria-hidden="true" /></span>
          <div>
            <h1>My profile</h1>
            <p>Manage the information used in your workspace.</p>
          </div>
          <button type="button" className="user-header-link" onClick={() => navigate("/rag")}>
            <Sparkles size={14} aria-hidden="true" />
            Planning companion
            <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>
      </header>

      <main className="product-main user-main">
        <section className="user-page-intro">
          <div>
            <p className="product-eyebrow">Your workspace</p>
            <h2>Keep your details up to date.</h2>
            <p>Your name and access status are used to personalize your planning workspace.</p>
          </div>
          <span className="user-intro-mark"><UserRound size={22} aria-hidden="true" /></span>
        </section>
        <UserProfile />
        <div className="user-help-row">
          <div><CalendarDays size={16} aria-hidden="true" /><span><strong>Workspace access</strong><small>Your planning tools are ready to use.</small></span></div>
          <button type="button" onClick={() => navigate("/rag")}><Sparkles size={16} aria-hidden="true" /><span><strong>Planning companion</strong><small>Save preferences and useful guidance for future plans.</small></span><ArrowRight size={15} aria-hidden="true" /></button>
        </div>
      </main>
    </div>
  );
}
