import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const UserBarriers: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [search, setSearch] = useState("");
  const [barriers, setBarriers] = useState<any[]>([]);
  const [ordering, setOrdering] = useState("");
  const [error, setError] = useState("");

  const [accessToken, setAccessToken] = useState(() =>
      location.state?.access_token || localStorage.getItem("access_token")
  );
  const [refreshToken, setRefreshToken] = useState(() =>
      location.state?.refresh_token || localStorage.getItem("refresh_token")
  );
  const phone = location.state?.phone || localStorage.getItem("phone");

  const fetchBarriers = async (token = accessToken) => {
    try {
      const params = new URLSearchParams({
        page: "1",
        page_size: "10",
      });
      if (ordering) params.append("ordering", ordering);
      if (search) params.append("search", search);

      const res = await fetch(`/api/barriers/my/?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
      });

      if (res.status === 401) {
        const refreshRes = await fetch("/auth/token/refresh/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: refreshToken }),
        });

        const refreshData = await refreshRes.json();
        if (refreshRes.ok && refreshData.access) {
          setAccessToken(refreshData.access);
          localStorage.setItem("access_token", refreshData.access);
          fetchBarriers(refreshData.access); // повторный вызов
        } else {
          navigate("/login");
        }
        return;
      }

      const data = await res.json();
      if (res.ok) {
        setBarriers(data.barriers || []);
      } else {
        setError("Ошибка загрузки данных");
      }
    } catch {
      setError("Ошибка сети");
    }
  };

  useEffect(() => {
    fetchBarriers();
  }, [search, ordering]);

  const handleOrdering = () => {
    if (ordering === "") setOrdering("address");
    else if (ordering === "address") setOrdering("-address");
    else setOrdering("");
  };

  return (
      <div style={styles.page}>
        <div style={styles.container}>
          <h1 style={styles.title}>🔍 Поиск шлагбаумов</h1>

          <div style={styles.searchContainer}>
            <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={styles.searchInput}
                placeholder="Введите название улицы..."
            />
            {search && (
                <button style={styles.clearButton} onClick={() => setSearch("")}>
                  ✕
                </button>
            )}
          </div>

          <button style={styles.filterButton} onClick={handleOrdering}>
            Сортировка {ordering === "address" ? "↑" : ordering === "-address" ? "↓" : ""}
          </button>

          {barriers.length > 0 ? (
              <ul style={styles.list}>
                {barriers.map((barrier, index) => (
                    <li
                        key={index}
                        style={styles.listItem}
                        onClick={() =>
                            navigate("/barrier-details", {
                              state: { barrier, phone, access_token: accessToken, refresh_token: refreshToken },
                            })
                        }
                    >
                      <strong>{barrier.address}</strong>
                      <p>📱 {barrier.device_phone}</p>
                      <p>ℹ️ {barrier.additional_info}</p>
                      <p>👤 {barrier.owner?.full_name || "Без владельца"}</p>
                    </li>
                ))}
              </ul>
          ) : (
              <p style={styles.noResults}>Нет результатов</p>
          )}

          {error && <p style={styles.errorText}>{error}</p>}
        </div>

        <div style={styles.navbar}>
          <button style={{ ...styles.navButton, ...styles.navButtonActive }}>Шлагбаумы</button>
          <button
              style={styles.navButton}
              onClick={() => navigate("/requests", { state: { phone, access_token: accessToken, refresh_token: refreshToken } })}
          >
            Запросы
          </button>
          <button
              style={styles.navButton}
              onClick={() => navigate("/user", { state: { phone, access_token: accessToken, refresh_token: refreshToken } })}
          >
            Профиль
          </button>
        </div>
      </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  page: {
    backgroundColor: "#fef7fb",
    minHeight: "100vh",
    width: "100vw",
    display: "flex",
    justifyContent: "center",
    paddingTop: "40px",
    boxSizing: "border-box",
  },
  container: {
    width: "100%",
    maxWidth: "500px",
    padding: "0 20px 100px",
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
  },
  title: {
    fontSize: "26px",
    textAlign: "center",
    marginBottom: "25px",
    color: "#5a4478",
    fontWeight: 700,
  },
  searchContainer: {
    display: "flex",
    alignItems: "center",
    width: "100%",
    marginBottom: "10px",
  },
  searchInput: {
    flex: 1,
    padding: "12px",
    fontSize: "16px",
    border: "1px solid #ccc",
    borderRadius: "8px",
    backgroundColor: "#ffffff",
    color: "#333",
    outline: "none",
  },
  clearButton: {
    marginLeft: "10px",
    padding: "10px 14px",
    backgroundColor: "#eae0f5",
    color: "#5a4478",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
  },
  filterButton: {
    marginTop: "5px",
    marginBottom: "15px",
    padding: "10px",
    backgroundColor: "#d7c4ed",
    color: "#5a4478",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold",
    alignSelf: "flex-start",
  },
  list: {
    listStyleType: "none",
    padding: 0,
    margin: 0,
    width: "100%",
  },
  listItem: {
    padding: "15px 20px",
    margin: "8px 0",
    backgroundColor: "#ffffff",
    borderRadius: "10px",
    cursor: "pointer",
    border: "1px solid #ddd",
    boxShadow: "0 2px 6px rgba(90, 68, 120, 0.1)",
    fontSize: "14px",
    color: "#333",
  },
  noResults: {
    marginTop: "10px",
    color: "#888",
    fontSize: "14px",
  },
  errorText: {
    color: "red",
    marginTop: "10px",
  },
  navbar: {
    display: "flex",
    justifyContent: "space-around",
    width: "100%",
    position: "fixed",
    bottom: "0",
    left: "50%",
    transform: "translateX(-50%)",
    backgroundColor: "#f8f3fb",
    padding: "12px 0",
    boxShadow: "0 -2px 10px rgba(0,0,0,0.05)",
    borderTop: "1px solid #ddd",
    maxWidth: "500px",
  },
  navButton: {
    background: "none",
    border: "none",
    fontSize: "14px",
    color: "#5a4478",
    cursor: "pointer",
    fontWeight: "bold",
    padding: "6px 12px",
  },
  navButtonActive: {
    borderBottom: "2px solid #5a4478",
    paddingBottom: "4px",
  },
};

export default UserBarriers;
