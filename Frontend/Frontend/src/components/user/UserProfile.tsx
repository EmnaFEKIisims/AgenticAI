// src/components/user/UserProfile.tsx

import { useState } from "react";
import {
  User as UserIcon,
  Pencil,
  Check,
  X,
  AlertCircle,
  ShieldCheck,
  CalendarDays,
  Loader2,
} from "lucide-react";
import { useUser } from "../../hooks/useUser";

export default function UserProfile() {
  const { user, isLoading, error, onUpdate } = useUser();
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) return;
    await onUpdate({ display_name: name.trim() });
    setEditing(false);
  };

  if (isLoading && !user) {
    return <div className="profile-card profile-loading"><Loader2 className="animate-spin" aria-hidden="true" /><span>Loading your profile…</span></div>;
  }

  return (
    <section className="profile-card">
      <div className="profile-card-top">
        <div className="profile-card-heading"><span className="profile-heading-icon"><UserIcon size={17} aria-hidden="true" /></span><div><p>Personal details</p><small>Information shown in your workspace</small></div></div>
        <span className="profile-status"><i /> {user?.is_active ? "Active" : "Unavailable"}</span>
      </div>

      <div className="profile-card-body">
        {error && <div className="profile-error"><AlertCircle size={15} aria-hidden="true" /><p>{error}</p></div>}

        <div className="profile-identity">
          <div className="profile-avatar">{(user?.display_name ?? "A")[0].toUpperCase()}</div>
          <div className="profile-identity-copy">
            <span className="profile-overline">Your name</span>
            {editing ? (
              <input autoFocus value={name} onChange={e => setName(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSave()} placeholder={user?.display_name} className="profile-name-input" />
            ) : <h2>{user?.display_name ?? "—"}</h2>}
            <span className="profile-role"><ShieldCheck size={13} aria-hidden="true" /> {user?.role === "admin" ? "Workspace owner" : "Workspace member"}</span>
          </div>
          <div className="profile-actions">
            {editing ? <><button type="button" className="profile-save-button" onClick={handleSave} disabled={isLoading}><Check size={14} aria-hidden="true" /> Save</button><button type="button" className="profile-cancel-button" onClick={() => setEditing(false)}><X size={14} aria-hidden="true" /> Cancel</button></> : <button type="button" className="profile-edit-button" onClick={() => { setEditing(true); setName(user?.display_name ?? ""); }}><Pencil size={14} aria-hidden="true" /> Edit name</button>}
          </div>
        </div>

        <div className="profile-details-grid">
          <div><span className="profile-detail-icon profile-detail-green"><Check size={15} aria-hidden="true" /></span><span><small>Workspace access</small><strong>{user?.is_active ? "Ready to use" : "Not available"}</strong></span></div>
          <div><span className="profile-detail-icon profile-detail-blue"><CalendarDays size={15} aria-hidden="true" /></span><span><small>Member since</small><strong>{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—"}</strong></span></div>
        </div>
      </div>
    </section>
  );
}