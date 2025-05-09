import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const AdminRequests: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [type, setType] = useState<"incoming" | "outgoing">("incoming");
  const [requests, setRequests] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(
    location.state?.access_token || localStorage.getItem("access_token"),
  );
  const [refreshToken] = useState(
    location.state?.refresh_token || localStorage.getItem("refresh_token"),
  );

  const fetchRequests = async (token = accessToken) => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/admin/access_requests/my/?type=${type}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401) {
        const refresh = await fetch("/api/auth/token/refresh/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: refreshToken }),
        });
        const newData = await refresh.json();
        if (refresh.ok && newData.access) {
          setAccessToken(newData.access);
          localStorage.setItem("access_token", newData.access);
          fetchRequests(newData.access);
        } else navigate("/login");
        return;
      }

      const data = await res.json();
      if (res.ok && data.access_requests) {
        const withBarriers = await Promise.all(
          data.access_requests.map(async (req: any) => {
            const resB = await fetch(`/api/barriers/${req.barrier}/`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const b = await resB.json();
            return { ...req, address: b.address || "Без адреса" };
          }),
        );
        setRequests(withBarriers);
      }
    } catch {
      console.error("Ошибка загрузки");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [type]);

  const updateRequestStatus = async (
    id: number,
    status: string,
    hide = false,
  ) => {
    try {
      await fetch(`/api/access_requests/${id}/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          status,
          ...(hide ? { hidden_for_user: true } : {}),
        }),
      });
      fetchRequests();
    } catch {
      console.error("Ошибка при обновлении запроса");
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Заявки</h2>

      <div style={styles.tabs}>
        <button
          style={{
            ...styles.tab,
            borderBottom: type === "incoming" ? "2px solid #5a4478" : "none",
          }}
          onClick={() => setType("incoming")}
        >
          Входящие
        </button>
        <button
          style={{
            ...styles.tab,
            borderBottom: type === "outgoing" ? "2px solid #5a4478" : "none",
          }}
          onClick={() => setType("outgoing")}
        >
          Исходящие
        </button>
      </div>

      <div style={styles.requestList}>
        {isLoading ? (
          <p>Загрузка...</p>
        ) : requests.length === 0 ? (
          <p>Нет запросов</p>
        ) : (
          requests.map((r) => (
            <div key={r.id} style={styles.card}>
              <p style={styles.text}>
                <strong>
                  {type === "incoming" ? r.requester_name : r.owner_name}
                </strong>
                <br />
                Адрес: {r.address}
              </p>

              {r.status === "pending" && type === "incoming" && (
                <div style={styles.actionRow}>
                  <button
                    style={styles.accept}
                    onClick={() => updateRequestStatus(r.id, "accepted")}
                  >
                    Принять
                  </button>
                  <button
                    style={styles.decline}
                    onClick={() => updateRequestStatus(r.id, "rejected")}
                  >
                    Отклонить
                  </button>
                </div>
              )}

              {r.status === "pending" && type === "outgoing" && (
                <button
                  style={styles.cancel}
                  onClick={() => updateRequestStatus(r.id, "cancelled", true)}
                >
                  Отменить
                </button>
              )}

              {r.status === "accepted" && <p style={styles.ok}>Принят</p>}
              {r.status === "rejected" && <p style={styles.err}>Отклонён</p>}
              {r.status === "cancelled" && <p style={styles.err}>Отменён</p>}
            </div>
          ))
        )}
      </div>

      <div style={styles.navbar}>
        <button
          style={styles.nav}
          onClick={() =>
            navigate("/admin-barriers", {
              state: { access_token: accessToken, refresh_token: refreshToken },
            })
          }
        >
          Шлагбаумы
        </button>
        <button style={{ ...styles.nav, ...styles.navActive }}>Запросы</button>
        <button
          style={styles.nav}
          onClick={() =>
            navigate("/admin", {
              state: { access_token: accessToken, refresh_token: refreshToken },
            })
          }
        >
          Профиль
        </button>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    width: "100vw",
    backgroundColor: "#fef7fb",
    color: "#333",
    padding: "20px",
  },
  title: {
    textAlign: "center",
    color: "#5a4478",
    fontSize: "24px",
    fontWeight: "bold",
    marginBottom: "20px",
  },
  tabs: {
    display: "flex",
    justifyContent: "center",
    gap: "10px",
    marginBottom: "20px",
  },
  tab: {
    background: "none",
    border: "none",
    fontSize: "16px",
    cursor: "pointer",
    fontWeight: "bold",
    color: "#5a4478",
    padding: "8px 16px",
  },
  requestList: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    maxWidth: "500px",
    margin: "0 auto",
  },
  card: {
    backgroundColor: "#fff",
    padding: "16px",
    borderRadius: "10px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.05)",
  },
  text: {
    fontSize: "16px",
    marginBottom: "10px",
  },
  actionRow: {
    display: "flex",
    gap: "10px",
    justifyContent: "center",
  },
  accept: {
    backgroundColor: "#5cb85c",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    padding: "8px 12px",
    cursor: "pointer",
  },
  decline: {
    backgroundColor: "#f0ad4e",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    padding: "8px 12px",
    cursor: "pointer",
  },
  cancel: {
    backgroundColor: "#d9534f",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    padding: "8px 12px",
    cursor: "pointer",
  },
  ok: {
    color: "green",
    fontWeight: "bold",
  },
  err: {
    color: "red",
    fontWeight: "bold",
  },
  navbar: {
    position: "fixed",
    bottom: 0,
    left: 0,
    width: "100%",
    backgroundColor: "#f8f3fb",
    padding: "10px 0",
    display: "flex",
    justifyContent: "space-around",
  },
  nav: {
    background: "none",
    border: "none",
    color: "#5a4478",
    fontSize: "14px",
    cursor: "pointer",
  },
  navActive: {
    borderBottom: "2px solid #5a4478",
    paddingBottom: "4px",
  },
};

export default AdminRequests;
