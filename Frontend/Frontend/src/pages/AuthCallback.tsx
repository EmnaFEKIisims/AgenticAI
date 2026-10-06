// src/pages/AuthCallback.tsx
// =============================
// Page atteinte après : backend /auth/login -> Keycloak -> Google/GitHub
// -> Keycloak -> backend /auth/callback -> ICI (avec access_token/refresh_token
// dans l'URL). On les stocke, on récupère le profil, puis on redirige.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { storeTokensFromCallback, fetchCurrentUser } from "../services/authService";

export default function AuthCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken  = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (!accessToken || !refreshToken) {
      setError("Tokens manquants dans l'URL de retour — le login a probablement échoué.");
      return;
    }

    storeTokensFromCallback(accessToken, refreshToken);

    fetchCurrentUser()
      .then(() => {
        navigate("/start", { replace: true });
      })
      .catch((err) => {
        setError(`Connecté, mais impossible de récupérer le profil : ${err.message}`);
      });
  }, [navigate]);

  if (error) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p>Erreur de connexion : {error}</p>
        <button onClick={() => navigate("/")}>Retour à l'accueil</button>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <p>Connexion en cours...</p>
    </div>
  );
}