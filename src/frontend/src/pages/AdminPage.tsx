import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const AdminPage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [password, setPassword] = useState("");
    const [balance, setBalance] = useState(100);
    const [isAdmin, setIsAdmin] = useState(true);

    const [accessToken] = useState(
        location.state?.access_token || localStorage.getItem("access_token")
    );
    const [refreshToken] = useState(
        location.state?.refresh_token || localStorage.getItem("refresh_token")
    );

    const handleBalanceCheck = () => {
        const randomBalance = Math.floor(Math.random() * 500);
        setBalance(randomBalance);
    };

    const handleSwitch = () => {
        setIsAdmin((prev) => {
            const newRole = !prev;
            if (!newRole) {
                navigate("/user", {
                    state: {
                        phone,
                        access_token: accessToken,
                        refresh_token: refreshToken,
                    },
                });
            }
            return newRole;
        });
    };

    const fetchUserData = async () => {
        try {
            const res = await fetch("/api/users/me/", {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                    Accept: "application/json",
                },
            });
            if (res.ok) {
                const data = await res.json();
                setName(data.full_name || "");
                setPhone(data.phone || "");
                setPassword(""); // Пароль пустой при получении
            } else if (res.status === 401) {
                const refreshRes = await fetch("/auth/token/refresh/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ refresh: refreshToken }),
                });
                const refreshData = await refreshRes.json();
                if (refreshRes.ok && refreshData.access) {
                    localStorage.setItem("access_token", refreshData.access);
                    window.location.reload();
                } else {
                    navigate("/login");
                }
            }
        } catch (error) {
            console.error("Ошибка при загрузке профиля:", error);
        }
    };

    useEffect(() => {
        fetchUserData();
    }, []);

    return (
        <div style={styles.page}>
            <div style={styles.wrapper}>
                <h1 style={styles.title}>Профиль администратора</h1>

                <EditableBlock label="Имя" value={name} setValue={setName} type="text" />
                <EditableBlock label="Телефон" value={phone} setValue={setPhone} type="text" />
                <EditableBlock label="Пароль" value={password} setValue={setPassword} type="password" />

                <div style={styles.card}>
                    <p style={styles.balanceText}>Баланс на счету: {balance} ₽</p>
                    <button style={styles.mainButton} onClick={handleBalanceCheck}>
                        Проверить баланс
                    </button>
                </div>

                <div style={styles.switchBlock}>
                    <span>Пользователь</span>
                    <label style={styles.switch}>
                        <input
                            type="checkbox"
                            checked={isAdmin}
                            onChange={handleSwitch}
                            style={styles.switchInput}
                        />
                        <span
                            style={{
                                ...styles.slider,
                                ...(isAdmin ? styles.switchChecked : {}),
                            }}
                        >
              <span
                  style={{
                      ...styles.sliderBefore,
                      ...(isAdmin ? styles.switchCheckedBefore : {}),
                  }}
              />
            </span>
                    </label>
                    <span>Администратор</span>
                </div>
            </div>

            <div style={styles.navbar}>
                <button style={styles.navButton} onClick={() => navigate("/barriers", { state: { phone, access_token: accessToken, refresh_token: refreshToken } })}>
                    Шлагбаумы
                </button>
                <button style={styles.navButton} onClick={() => navigate("/requests", { state: { phone, access_token: accessToken, refresh_token: refreshToken } })}>
                    Запросы
                </button>
                <button style={{ ...styles.navButton, ...styles.activeNavButton }}>
                    Профиль
                </button>
            </div>
        </div>
    );
};

const EditableBlock = ({
                           label,
                           value,
                           setValue,
                           type,
                       }: {
    label: string;
    value: string;
    setValue: (val: string) => void;
    type: string;
}) => {
    const [editing, setEditing] = useState(false);

    return (
        <div style={styles.card}>
            {editing ? (
                <div style={{ position: "relative" }}>
                    <input
                        type={type}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        style={styles.input}
                    />
                    {type !== "password" && value && (
                        <button
                            onClick={() => setValue("")}
                            style={styles.clearButton}
                        >
                            ✕
                        </button>
                    )}
                </div>
            ) : (
                <p style={styles.text}>{type === "password" && !value ? "••••••" : value}</p>
            )}
            <button
                style={styles.mainButton}
                onClick={() => setEditing((prev) => !prev)}
            >
                {editing ? "Сохранить" : `Изменить ${label.toLowerCase()}`}
            </button>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    page: {
        backgroundColor: "#fef7fb",
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingBottom: "100px",
        fontFamily: "sans-serif",
    },
    wrapper: {
        marginTop: "30px",
        width: "100%",
        maxWidth: "400px",
        padding: "0 20px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
    },
    title: {
        fontSize: "26px",
        fontWeight: "bold",
        color: "#5a4478",
        marginBottom: "30px",
        textAlign: "center",
    },
    card: {
        backgroundColor: "#ffffff",
        padding: "20px",
        borderRadius: "16px",
        boxShadow: "0 4px 15px rgba(90, 68, 120, 0.2)",
        textAlign: "center",
        width: "100%",
        marginBottom: "20px",
        position: "relative",
    },
    text: {
        fontSize: "18px",
        fontWeight: 500,
        marginBottom: "10px",
        color: "#333",
    },
    input: {
        width: "100%",
        padding: "12px",
        fontSize: "16px",
        borderRadius: "10px",
        border: "1px solid #ccc",
        outline: "none",
        backgroundColor: "#ffffff",
        textAlign: "center",
        color: "#333",
    },
    clearButton: {
        position: "absolute",
        right: "15px",
        top: "8px",
        background: "none",
        border: "none",
        fontSize: "18px",
        color: "#5a4478",
        cursor: "pointer",
    },
    mainButton: {
        marginTop: "15px",
        width: "100%",
        backgroundColor: "#5a4478",
        color: "#ffffff",
        border: "none",
        padding: "12px",
        borderRadius: "25px",
        fontSize: "14px",
        cursor: "pointer",
        fontWeight: "bold",
    },
    balanceText: {
        fontSize: "16px",
        color: "#5a4478",
        marginBottom: "10px",
    },
    switchBlock: {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginTop: "25px",
        gap: "10px",
        color: "#5a4478",
        fontSize: "14px",
    },
    switch: {
        position: "relative",
        display: "inline-block",
        width: "50px",
        height: "24px",
    },
    switchInput: {
        opacity: 0,
        width: 0,
        height: 0,
    },
    slider: {
        position: "absolute",
        cursor: "pointer",
        top: "0",
        left: "0",
        right: "0",
        bottom: "0",
        backgroundColor: "#ccc",
        borderRadius: "24px",
        transition: "0.4s",
    },
    sliderBefore: {
        position: "absolute",
        content: "''",
        height: "18px",
        width: "18px",
        left: "3px",
        bottom: "3px",
        backgroundColor: "white",
        transition: "0.4s",
        borderRadius: "50%",
    },
    switchChecked: {
        backgroundColor: "#5a4478",
    },
    switchCheckedBefore: {
        transform: "translateX(26px)",
    },
    navbar: {
        display: "flex",
        justifyContent: "space-around",
        width: "100%",
        position: "fixed",
        bottom: "0",
        backgroundColor: "#f8f3fb",
        padding: "12px 0",
        boxShadow: "0 -2px 10px rgba(0,0,0,0.05)",
    },
    navButton: {
        background: "none",
        border: "none",
        fontSize: "14px",
        color: "#5a4478",
        cursor: "pointer",
        fontWeight: "bold",
    },
    activeNavButton: {
        borderBottom: "2px solid #5a4478",
        paddingBottom: "4px",
    },
};

export default AdminPage;
