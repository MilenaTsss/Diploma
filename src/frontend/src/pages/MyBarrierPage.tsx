import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    FaArrowLeft,
    FaTrash,
    FaEdit,
    FaCheckCircle,
    FaExclamationCircle,
    FaClock,
    FaCalendarAlt,
} from "react-icons/fa";

const MyBarrierPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const barrierId = location.state?.barrier_id;
    const accessTokenInit = location.state?.access_token || localStorage.getItem("access_token");
    const refreshToken = location.state?.refresh_token || localStorage.getItem("refresh_token");

    const [accessToken, setAccessToken] = useState(accessTokenInit);
    const [barrier, setBarrier] = useState<any>(null);
    const [user, setUser] = useState<any>(null);
    const [limits, setLimits] = useState<any>(null);
    const [phones, setPhones] = useState<any[]>([]);
    const [error, setError] = useState("");

    const fetchWithAuth = async (url: string, token: string): Promise<any> => {
        const res = await fetch(url, {
            headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
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
                return fetchWithAuth(url, refreshData.access);
            } else {
                navigate("/login");
                return null;
            }
        }

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Ошибка загрузки");
        return data;
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [barrierData, userData, limitsData, phonesData] = await Promise.all([
                    fetchWithAuth(`/api/barriers/${barrierId}/`, accessToken),
                    fetchWithAuth("/api/users/me/", accessToken),
                    fetchWithAuth(`/api/barriers/${barrierId}/limits/`, accessToken),
                    fetchWithAuth(`/api/barriers/${barrierId}/phones/my/`, accessToken),
                ]);
                setBarrier(barrierData);
                setUser(userData);
                setLimits(limitsData);
                setPhones(phonesData.phones || []);
            } catch (e: any) {
                setError(e.message);
            }
        };
        fetchData();
    }, [barrierId]);

    const handleDelete = async (phoneId: number) => {
        if (!window.confirm("Удалить этот номер?")) return;

        try {
            const res = await fetch(`/api/phones/${phoneId}/`, {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    Accept: "application/json",
                },
            });

            if (res.ok) {
                setPhones((prev) => prev.filter((p) => p.id !== phoneId));
            } else {
                const data = await res.json();
                alert(data.detail || "Ошибка удаления номера");
            }
        } catch {
            alert("Ошибка сети при удалении");
        }
    };


    if (error) return <p style={{ color: "red", padding: "5vw" }}>{error}</p>;
    if (!barrier || !user) return <p style={{ padding: "5vw" }}>Загрузка...</p>;

    return (
        <div style={styles.page}>
            <div style={styles.inner}>
                <div style={styles.contentWrapper}>
                    <div style={styles.header}>
                        <button onClick={() => navigate(-1)} style={styles.backButton}>
                            <FaArrowLeft />
                        </button>
                        <h1 style={styles.title}>{barrier.address}</h1>
                    </div>

                    <div style={styles.card}>
                        <p><strong>Администратор:</strong> {barrier.owner.full_name}</p>
                        <p><strong>Телефон шлагбаума:</strong> {barrier.device_phone}</p>
                        <p><strong>Телефон администратора:</strong> {barrier.owner.phone || "не указано"}</p>
                    </div>

                    <div style={styles.card}>
                        <h3 style={styles.subtitle}>Лимиты шлагбаума:</h3>
                        {limits && (
                            <>
                                <p>Обычные номера: {limits.user_phone_limit}</p>
                                <p>Временные номера (пользователь): {limits.user_temp_phone_limit}</p>
                                <p>Временные номера (всего): {limits.global_temp_phone_limit}</p>
                                <p>Номера по расписанию (пользователь): {limits.user_schedule_phone_limit}</p>
                                <p>Номера по расписанию (всего): {limits.global_schedule_phone_limit}</p>
                                <p>Ограничение интервалов расписания: {limits.schedule_interval_limit}</p>
                                <p>СМС в неделю: {limits.sms_weekly_limit}</p>
                            </>

                        )}
                    </div>

                    <div style={styles.card}>
                        <h3 style={styles.subtitle}>Основной номер:</h3>
                        <p>{user.full_name} — {user.phone}</p>
                    </div>

                    <div style={styles.card}>
                        <h3 style={styles.subtitle}>Дополнительные номера:</h3>
                        {phones.length === 0 ? (
                            <p>Нет дополнительных номеров</p>
                        ) : (
                            phones.map((item) => (
                                <div key={item.id} style={styles.phoneRow}>
                                    <div style={styles.phoneHeader}>
                                        <p style={styles.phoneText}>
                                            <strong>{item.name}</strong> — {item.phone}
                                        </p>
                                        <div style={styles.iconGroup}>
                                            <FaEdit
                                                style={styles.icon}
                                                onClick={() =>
                                                    navigate("/edit-phone", {
                                                        state: {
                                                            phone_id: item.id,
                                                            phone_data: item,
                                                            access_token: accessToken,
                                                            barrier_id: barrier.id,
                                                            refresh_token: refreshToken,

                                                        }
                                                    })
                                                }
                                            />
                                            <FaTrash style={styles.icon} onClick={() => handleDelete(item.id)} />
                                            {item.type === "temporary" && <FaClock style={styles.icon} />}
                                            {item.type === "schedule" && <FaCalendarAlt style={styles.icon} />}
                                            {item.status === "error" && (
                                                <FaExclamationCircle style={{ ...styles.icon, color: "#d9534f" }} />
                                            )}
                                            {item.status === "ok" && (
                                                <FaCheckCircle style={{ ...styles.icon, color: "green" }} />
                                            )}
                                        </div>
                                    </div>
                                    {(item.type === "temporary" || item.type === "schedule") && (
                                        <p style={styles.timeInfo}>
                                            {item.type === "temporary" ? (
                                                <>
                                                    Начало: {new Date(item.start_time).toLocaleString()}<br />
                                                    Конец: {new Date(item.end_time).toLocaleString()}
                                                </>
                                            ) : (
                                                <>
                                                    Начало: Пн 10:00<br />
                                                    Конец: Ср 18:00
                                                </>
                                            )}
                                        </p>
                                    )}
                                </div>
                            ))
                        )}
                    </div>

                    <div style={{ display: "flex", gap: "10px", marginTop: "20px", flexDirection: "column" }}>
                        <button
                            style={styles.button}
                            onClick={() =>
                                navigate("/add-phone", {
                                    state: {
                                        barrier_id: barrier.id,
                                        access_token: accessToken,
                                        refresh_token: refreshToken, // если нужно
                                    },
                                })
                            }
                        >
                            Добавить номер
                        </button>

                        <button style={{ ...styles.button, backgroundColor: "#d7c4ed" }}>История изменений</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    page: {
        backgroundColor: "#fef7fb",
        minHeight: "100vh",
        width: "100vw",
        padding: "5vw",
        fontFamily: "sans-serif",
        boxSizing: "border-box",
    },
    header: {
        display: "flex",
        alignItems: "center",
        gap: "10px",
        marginBottom: "20px",
    },
    backButton: {
        background: "none",
        border: "none",
        fontSize: "clamp(18px, 4vw, 24px)",
        color: "#5a4478",
        cursor: "pointer",
    },
    title: {
        fontSize: "clamp(20px, 5vw, 26px)",
        fontWeight: "bold",
        color: "#5a4478",
    },
    card: {
        backgroundColor: "#fff",
        padding: "clamp(16px, 4vw, 24px)",
        borderRadius: "12px",
        boxShadow: "0 4px 10px rgba(90, 68, 120, 0.1)",
        marginBottom: "20px",
        width: "100%",             // адаптивная ширина
        maxWidth: "500px",         // максимум ширины карточки
        marginLeft: "auto",        // центрирование по горизонтали
        marginRight: "auto",
    },
    subtitle: {
        color: "#5a4478",
        fontWeight: "bold",
        fontSize: "clamp(16px, 4vw, 20px)",
        marginBottom: "10px",
    },
    button: {
        width: "50%",
        backgroundColor: "#5a4478",
        color: "#fff",
        padding: "14px",
        borderRadius: "20px",
        border: "none",
        cursor: "pointer",
        fontWeight: "bold",
        fontSize: "clamp(14px, 4vw, 16px)",
        boxSizing: "border-box",
        margin: "0 auto", // центрирует по горизонтали
    },
    phoneRow: {
        marginTop: "12px",
        paddingTop: "10px",
        borderTop: "1px solid #eee",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
    },
    phoneHeader: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "10px",
    },
    phoneText: {
        fontSize: "clamp(14px, 3.5vw, 16px)",
        color: "#333",
        margin: 0,
    },
    iconGroup: {
        display: "flex",
        alignItems: "center",
        gap: "6px",
    },
    icon: {
        fontSize: "16px",
        color: "#5a4478",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
    timeInfo: {
        fontSize: "12px",
        color: "#666",
        marginLeft: "4px",
    },
    inner: {},
    contentWrapper: {},
};

export default MyBarrierPage;
