import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        padding: 20,
        fontFamily: "sans-serif",
        backgroundColor: "#fff6fa",
        minHeight: "100vh",
    },
    backButton: {
        marginBottom: 20,
        color: "#5a4478",
        background: "none",
        border: "none",
        cursor: "pointer",
        fontSize: "16px",
    },
    title: {
        textAlign: "center",
        color: "#5a4478",
        fontSize: "24px",
        fontWeight: "bold",
        marginBottom: 20,
    },
    select: {
        width: "100%",
        maxWidth: 400,
        padding: 10,
        fontSize: 16,
        borderRadius: 8,
        border: "1px solid #ccc",
        margin: "0 auto 20px",
        display: "block",
        backgroundColor: "#fff",
        color: "#5a4478",
        fontWeight: 600,
    },
    settingCard: {
        maxWidth: 500,
        background: "white",
        padding: 20,
        borderRadius: 10,
        boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        margin: "0 auto",
    },
    settingName: {
        fontSize: "18px",
        fontWeight: 600,
        marginBottom: 6,
    },
    settingDesc: {
        fontSize: 14,
        color: "#555",
        marginBottom: 12,
    },
    inputBlock: {
        marginBottom: 10,
    },
    label: {
        fontWeight: 600,
        display: "block",
        marginBottom: 4,
    },
    input: {
        width: "100%",
        padding: 8,
        borderRadius: 8,
        border: "1px solid #ccc",
        boxSizing: "border-box",
    },
    submitButton: {
        padding: "8px 16px",
        backgroundColor: "#5a4478",
        color: "white",
        border: "none",
        borderRadius: 8,
        cursor: "pointer",
    },
    preview: {
        backgroundColor: "#f0ebfa",
        color: "#333",
        padding: 10,
        borderRadius: 8,
        fontSize: 14,
        fontFamily: "monospace",
        marginTop: 12,
        whiteSpace: "pre-wrap",
    },
    error: {
        color: "red",
        textAlign: "center",
        marginTop: 10,
    },
    success: {
        color: "green",
        textAlign: "center",
        marginTop: 10,
    },
};

const AdminBarrierSettingsPage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const accessToken = location.state?.access_token || localStorage.getItem("access_token");
    const refreshToken = location.state?.refresh_token || localStorage.getItem("refresh_token");
    const barrierId = location.state?.barrier_id;

    const [settings, setSettings] = useState<any>({});
    const [formValues, setFormValues] = useState<any>({});
    const [selectedKey, setSelectedKey] = useState<string>("");
    const [success, setSuccess] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await fetch(`/api/admin/barriers/${barrierId}/settings/`, {
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        Accept: "application/json",
                    },
                });
                const data = await res.json();
                if (res.ok) {
                    setSettings(data.settings || {});
                    const firstKey = Object.keys(data.settings)[0];
                    setSelectedKey(firstKey);
                } else {
                    setError("Ошибка при загрузке настроек");
                }
            } catch {
                setError("Ошибка сети");
            }
        };
        fetchSettings();
    }, [barrierId]);

    const handleChange = (settingKey: string, paramKey: string, value: string) => {
        setFormValues((prev: any) => ({
            ...prev,
            [settingKey]: {
                ...prev[settingKey],
                [paramKey]: value,
            },
        }));
    };

    const handleSubmit = async (settingKey: string) => {
        setError("");
        setSuccess("");
        try {
            const res = await fetch(`/api/admin/barriers/${barrierId}/settings/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                },
                body: JSON.stringify({
                    setting: settingKey,
                    params: formValues[settingKey] || {},
                }),
            });
            const data = await res.json();
            if (res.ok) {
                setSuccess(`Настройка '${settingKey}' успешно отправлена.`);
            } else {
                setError(data.detail || "Ошибка при отправке настройки.");
            }
        } catch {
            setError("Ошибка сети при отправке настройки.");
        }
    };

    const currentSetting = settings[selectedKey];

    const getPreviewCommand = () => {
        if (!currentSetting || !currentSetting.template) return "";
        return currentSetting.template.replace(/\{(\w+)\}/g, (match: string, key: string) =>
            formValues[selectedKey]?.[key] || `{${key}}`
        );
    };

    return (
        <div style={styles.container}>
            <button onClick={() => navigate("/admin-barriers", { state: { access_token: accessToken, refresh_token: refreshToken } })} style={styles.backButton}>
                ← Назад
            </button>
            <h2 style={styles.title}>Настройки шлагбаума</h2>

            <select value={selectedKey} onChange={(e) => setSelectedKey(e.target.value)} style={styles.select}>
                {Object.entries(settings).map(([key, setting]: any) => (
                    <option key={key} value={key}>{setting.name}</option>
                ))}
            </select>

            {currentSetting && (
                <div style={styles.settingCard}>
                    <h3 style={styles.settingName}>{currentSetting.name}</h3>
                    <p style={styles.settingDesc}>{currentSetting.description}</p>
                    {currentSetting.params.map((param: any) => (
                        <div key={param.key} style={styles.inputBlock}>
                            <label style={styles.label}>{param.name}</label>
                            <input
                                type="text"
                                placeholder={param.description}
                                value={formValues[selectedKey]?.[param.key] || ""}
                                onChange={(e) => handleChange(selectedKey, param.key, e.target.value)}
                                style={styles.input}
                            />
                        </div>
                    ))}
                    <button
                        onClick={() => handleSubmit(selectedKey)}
                        style={styles.submitButton}
                    >
                        Отправить
                    </button>
                    {currentSetting.template && (
                        <div style={styles.preview}>
                            <strong>Команда:</strong> {getPreviewCommand()}
                        </div>
                    )}
                </div>
            )}

            {error && <p style={styles.error}>{error}</p>}
            {success && <p style={styles.success}>{success}</p>}
        </div>
    );
};

export default AdminBarrierSettingsPage;
