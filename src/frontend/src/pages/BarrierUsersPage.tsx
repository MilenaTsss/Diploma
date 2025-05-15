import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const BarrierUsersPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { barrier_id } = location.state || {};
  const [accessToken, setAccessToken] = useState(
    location.state?.access_token || localStorage.getItem("access_token"),
  );
  const refreshToken =
    location.state?.refresh_token || localStorage.getItem("refresh_token");

  const [barrierName, setBarrierName] = useState("Загрузка...");
  const [users, setUsers] = useState<any[]>([]);
  const [ordering, setOrdering] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState("");
  const [blockReason, setBlockReason] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [blockErrors, setBlockErrors] = useState<Record<number, string>>({});
  const [deleteErrors, setDeleteErrors] = useState<Record<number, string>>({});
  const [showReasonInput, setShowReasonInput] = useState<
    Record<number, boolean>
  >({});

  const fetchBarrierInfo = async () => {
    try {
      const res = await fetch(`/api/admin/barriers/${barrier_id}/`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (res.ok) setBarrierName(data.address);
    } catch {}
  };

  const fetchUsers = async (token = accessToken) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: "10",
    });
    if (ordering) params.append("ordering", ordering);
    if (search.trim()) params.append("search", search.trim());

    try {
      const res = await fetch(
        `/api/admin/barriers/${barrier_id}/users/?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        },
      );

      if (res.status === 401) return await refreshAndRetry();

      const data = await res.json();
      if (res.ok) {
        setUsers(data.users || []);
        setTotalPages(Math.ceil(data.total_count / 10));
      } else {
        setError("Ошибка загрузки пользователей");
      }
    } catch {
      setError("Ошибка сети при загрузке пользователей");
    }
  };

  const refreshAndRetry = async () => {
    try {
      const res = await fetch("/api/auth/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
      });
      const data = await res.json();
      if (res.ok && data.access) {
        setAccessToken(data.access);
        localStorage.setItem("access_token", data.access);
        fetchUsers(data.access);
      } else {
        navigate("/login");
      }
    } catch {
      setError("Ошибка обновления токена");
    }
  };

  const handleOrdering = () => {
    if (ordering === "") setOrdering("full_name");
    else if (ordering === "full_name") setOrdering("-full_name");
    else setOrdering("");
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm("Удалить пользователя из шлагбаума?")) return;
    try {
      const res = await fetch(
        `/api/admin/barriers/${barrier_id}/users/${userId}/`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${accessToken}` },
        },
      );
      if (res.ok) {
        setUsers((prev) => prev.filter((u) => u.id !== userId));
        setDeleteErrors((prev) => ({ ...prev, [userId]: "" }));
      } else {
        const data = await res.json();
        setDeleteErrors((prev) => ({
          ...prev,
          [userId]: data.detail || "Ошибка удаления пользователя.",
        }));
      }
    } catch {
      setDeleteErrors((prev) => ({
        ...prev,
        [userId]: "Ошибка сети при удалении.",
      }));
    }
  };

  const handleBlockUser = async (userId: number) => {
    if (!blockReason.trim()) {
      setBlockErrors((prev) => ({
        ...prev,
        [userId]: "Укажите причину блокировки.",
      }));
      return;
    }
    try {
      const res = await fetch(`/api/admin/users/${userId}/block/`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason: blockReason }),
      });
      if (res.ok) {
        setBlockErrors((prev) => ({ ...prev, [userId]: "" }));
        setBlockReason("");
        setSelectedUserId(null);
        setShowReasonInput((prev) => ({ ...prev, [userId]: false }));
        fetchUsers();
      } else {
        const data = await res.json();
        setBlockErrors((prev) => ({
          ...prev,
          [userId]: data.detail || "Ошибка блокировки.",
        }));
      }
    } catch {
      setBlockErrors((prev) => ({
        ...prev,
        [userId]: "Ошибка сети при блокировке.",
      }));
    }
  };

  useEffect(() => {
    fetchBarrierInfo();
  }, []);
  useEffect(() => {
    fetchUsers();
  }, [ordering, page, search]);

  return (
    <div style={styles.container}>
      <button
        style={styles.backButton}
        onClick={() =>
          navigate("/admin-barrier-page", {
            state: {
              barrier_id,
              access_token: accessToken,
              refresh_token: refreshToken,
            },
          })
        }
      >
        ← Назад к шлагбауму
      </button>

      <h2 style={styles.title}>Пользователи: {barrierName}</h2>

      <div style={styles.controls}>
        <button style={styles.orderButton} onClick={handleOrdering}>
          Сортировка{" "}
          {ordering === "full_name"
            ? "↑"
            : ordering === "-full_name"
              ? "↓"
              : ""}
        </button>
      </div>

      {users.length > 0 ? (
        <ul style={styles.list}>
          {users.map((user) => (
            <li key={user.id} style={styles.userCard}>
              <p>
                <strong>{user.full_name}</strong>
              </p>
              <p>{user.phone}</p>
              <p>Роль: {user.role}</p>
              <p style={{ color: user.is_active ? "green" : "gray" }}>
                {user.is_active ? "Активен" : "Заблокирован"}
              </p>

              <button
                style={styles.button}
                onClick={() =>
                  navigate("/user-profile", {
                    state: {
                      user_id: user.id,
                      access_token: accessToken,
                      refresh_token: refreshToken,
                      barrier_id,
                    },
                  })
                }
              >
                Перейти к пользователю
              </button>

              <button
                style={{
                  ...styles.button,
                  backgroundColor: "#ffe3e3",
                  color: "#d9534f",
                }}
                onClick={() => handleDeleteUser(user.id)}
              >
                Удалить из шлагбаума
              </button>
              {deleteErrors[user.id] && (
                <p style={styles.error}>{deleteErrors[user.id]}</p>
              )}

              {!showReasonInput[user.id] ? (
                <button
                  style={{
                    ...styles.button,
                    backgroundColor: "#f0d9ff",
                    color: "#5a4478",
                  }}
                  onClick={() => {
                    setShowReasonInput((prev) => ({
                      ...prev,
                      [user.id]: true,
                    }));
                    setSelectedUserId(user.id);
                  }}
                >
                  Заблокировать пользователя
                </button>
              ) : (
                <div>
                  <input
                    placeholder="Причина блокировки"
                    value={selectedUserId === user.id ? blockReason : ""}
                    onChange={(e) => {
                      setSelectedUserId(user.id);
                      setBlockReason(e.target.value);
                    }}
                    style={styles.input}
                  />
                  <button
                    style={{
                      ...styles.button,
                      backgroundColor: "#d9534f",
                      color: "white",
                    }}
                    onClick={() => handleBlockUser(user.id)}
                  >
                    Подтвердить блокировку
                  </button>
                  {blockErrors[user.id] && (
                    <p style={styles.error}>{blockErrors[user.id]}</p>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p style={styles.error}>Нет пользователей</p>
      )}

      <div style={styles.pagination}>
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page === 1}
        >
          ← Назад
        </button>
        <span>
          {page} / {totalPages}
        </span>
        <button
          onClick={() => setPage(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
        >
          Вперёд →
        </button>
      </div>

      {error && <p style={styles.error}>{error}</p>}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    backgroundColor: "#fff6fb",
    minHeight: "100vh",
    width: "100vw",
    padding: "5vw",
    fontFamily: "sans-serif",
  },
  title: {
    textAlign: "center",
    color: "#5a4478",
    marginBottom: "20px",
  },
  backButton: {
    background: "transparent",
    border: "none",
    color: "#5a4478",
    cursor: "pointer",
    fontSize: "16px",
    marginBottom: "10px",
  },
  controls: {
    display: "flex",
    gap: "10px",
    marginBottom: "10px",
  },
  orderButton: {
    backgroundColor: "#d7c4ed",
    color: "#5a4478",
    border: "none",
    padding: "10px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  list: {
    listStyle: "none",
    padding: 0,
  },
  userCard: {
    backgroundColor: "#fff",
    padding: "clamp(16px, 4vw, 24px)",
    borderRadius: "12px",
    boxShadow: "0 4px 10px rgba(90, 68, 120, 0.1)",
    marginBottom: "20px",
    width: "100%",
    maxWidth: "500px",
    marginLeft: "auto",
    marginRight: "auto",
  },
  button: {
    marginTop: "8px",
    padding: "6px 10px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    backgroundColor: "#d7c4ed",
    color: "#5a4478",
  },
  input: {
    width: "100%",
    marginTop: "6px",
    padding: "8px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    fontSize: "14px",
    boxSizing: "border-box",
  },
  pagination: {
    display: "flex",
    justifyContent: "center",
    gap: "20px",
    marginTop: "20px",
  },
  error: {
    color: "red",
    fontSize: "13px",
    marginTop: "6px",
  },
};

export default BarrierUsersPage;
