import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const AdminUserProfile: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { user_id, barrier_id } = location.state || {};
    const [accessToken, setAccessToken] = useState(location.state?.access_token || localStorage.getItem("access_token"));
    const refreshToken = location.state?.refresh_token || localStorage.getItem("refresh_token");

    const [user, setUser] = useState<any>(null);
    const [phones, setPhones] = useState<any[]>([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [error, setError] = useState("");

    const fetchWithAuth = async (url: string, token: string): Promise<any> => {
        const res = await fetch(url, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.status === 401) return await refreshTokenAndRetry(url);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Ошибка запроса");
        return data;
    };

    const refreshTokenAndRetry = async (url: string) => {
        const res = await fetch("/api/auth/token/refresh/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
        });
        const data = await res.json();
        if (res.ok && data.access) {
            setAccessToken(data.access);
            localStorage.setItem("access_token", data.access);
            return await fetchWithAuth(url, data.access);
        } else {
            navigate("/login");
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const userData = await fetchWithAuth(`/api/admin/users/${user_id}/`, accessToken);
                const phonesData = await fetchWithAuth(`/api/admin/barriers/${barrier_id}/phones/my/?user=${user_id}&page=${page}&page_size=10`, accessToken);
                setUser(userData);
                setPhones(phonesData.phones || []);
                setTotalPages(Math.ceil(phonesData.total_count / 10));
            } catch (e: any) {
                setError(e.message);
            }
        };
        fetchData();
    }, [user_id, page]);

    if (error) return <p style={styles.error}>{error}</p>;
    if (!user) return <p style={styles.loading}>Загрузка...</p>;

    return (
        <div style={styles.container}>
            <button
                style={styles.backButton}
                onClick={() => navigate("/barrier-users", {
                    state: { barrier_id, access_token: accessToken, refresh_token: refreshToken },
                })}
            >
                ← Назад к пользователям
            </button>

            <h2 style={styles.title}>{user.full_name}</h2>
            <p><strong>Телефон:</strong> {user.phone}</p>
            <p><strong>Роль:</strong> {user.role}</p>
            <p><strong>Статус:</strong> {user.is_active ? "Активен" : "Заблокирован"}</p>
            <p><strong>Приватность телефона:</strong> {user.phone_privacy}</p>

            <h3 style={styles.subtitle}>Дополнительные номера</h3>
            {phones.length === 0 ? (
                <p>Нет номеров</p>
            ) : (
                <ul style={styles.list}>
                    {phones.map((phone) => (
                        <li key={phone.id} style={styles.card}>
                            <p><strong>{phone.name}</strong> — {phone.phone}</p>
                            <p>Тип: {phone.type}</p>
                            <p>Активен: {phone.is_active ? "Да" : "Нет"}</p>
                        </li>
                    ))}
                </ul>
            )}

            <div style={styles.pagination}>
                <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
                    ← Назад
                </button>
                <span>{page} / {totalPages}</span>
                <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages}>
                    Вперёд →
                </button>
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        backgroundColor: "#fef7fb",
        minHeight: "100vh",
        padding: "20px",
        fontFamily: "sans-serif",
    },
    title: {
        fontSize: "22px",
        color: "#5a4478",
        marginBottom: "10px",
    },
    subtitle: {
        marginTop: "20px",
        color: "#5a4478",
    },
    backButton: {
        background: "transparent",
        border: "none",
        color: "#5a4478",
        cursor: "pointer",
        fontSize: "16px",
        marginBottom: "10px",
    },
    list: {
        listStyle: "none",
        padding: 0,
    },
    card: {
        backgroundColor: "#fff",
        padding: "15px",
        borderRadius: "10px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        marginBottom: "10px",
    },
    pagination: {
        display: "flex",
        justifyContent: "center",
        gap: "20px",
        marginTop: "20px",
    },
    error: {
        textAlign: "center",
        color: "red",
        marginTop: "10px",
    },
    loading: {
        textAlign: "center",
        color: "#5a4478",
        marginTop: "10px",
    },
};

export default AdminUserProfile;
