import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const AdminPage: React.FC = () => {
    const navigate = useNavigate();

    const [name, setName] = useState("Иванов Иван");
    const [phone, setPhone] = useState("+7 (999) 999-09-91");
    const [password, setPassword] = useState("aa12354");
    const [balance, setBalance] = useState(100);
    const [isAdmin, setIsAdmin] = useState(false);

    return (
        <div style={styles.page}>
            <div style={styles.container}>
                <InputBlock
                    value={name}
                    onChange={setName}
                    buttonText="Изменить имя в профиле"
                />

                <InputBlock
                    value={phone}
                    onChange={setPhone}
                    buttonText="Изменить номер телефона"
                />

                <InputBlock
                    value={password}
                    onChange={setPassword}
                    buttonText="Изменить пароль"
                />

                <div style={styles.balanceSection}>
                    <p style={styles.balanceText}>Баланс на счету - {balance} rub</p>
                    <button style={styles.actionButton}>Проверить баланс</button>
                </div>

                <div style={styles.switchSection}>
                    <span>Пользователь</span>
                    <label style={styles.switch}>
                        <input
                            type="checkbox"
                            checked={isAdmin}
                            onChange={() => setIsAdmin((prev) => !prev)}
                        />
                        <span style={styles.slider}></span>
                    </label>
                    <span>Администратор</span>
                </div>
            </div>

            <div style={styles.navbar}>
                <button style={styles.navButton} onClick={() => navigate("/barriers")}>
                    Шлагбаумы
                </button>
                <button style={styles.navButton} onClick={() => navigate("/requests")}>
                    Запросы
                </button>
                <button style={{ ...styles.navButton, ...styles.activeNavButton }}>
                    Профиль
                </button>
            </div>
        </div>
    );
};

const InputBlock = ({
                        value,
                        onChange,
                        buttonText,
                    }: {
    value: string;
    onChange: (val: string) => void;
    buttonText: string;
}) => (
    <div style={styles.inputBlock}>
        <div style={styles.inputContainer}>
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                style={styles.input}
            />
            {value && (
                <button onClick={() => onChange("")} style={styles.clearButton}>
                    ✕
                </button>
            )}
        </div>
        <button style={styles.actionButton}>{buttonText}</button>
    </div>
);

const styles: { [key: string]: React.CSSProperties } = {
    page: {
        backgroundColor: "#fef7fb",
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: "20px",
        paddingBottom: "100px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
    },
    container: {
        width: "100%",
        maxWidth: "400px",
        padding: "0 20px",
    },
    inputBlock: {
        marginBottom: "20px",
    },
    inputContainer: {
        position: "relative",
    },
    input: {
        width: "100%",
        padding: "12px",
        fontSize: "16px",
        border: "1px solid #ccc",
        borderRadius: "8px",
        backgroundColor: "#ffffff",
        color: "#333",
        outline: "none",
        boxSizing: "border-box",
    },
    clearButton: {
        position: "absolute",
        right: "10px",
        top: "50%",
        transform: "translateY(-50%)",
        background: "none",
        border: "none",
        fontSize: "16px",
        color: "#5a4478",
        cursor: "pointer",
    },
    actionButton: {
        marginTop: "8px",
        backgroundColor: "#5a4478",
        color: "#ffffff",
        border: "none",
        padding: "12px",
        borderRadius: "25px",
        cursor: "pointer",
        width: "100%",
        fontSize: "14px",
    },
    balanceSection: {
        marginTop: "20px",
        textAlign: "center",
    },
    balanceText: {
        marginBottom: "10px",
        color: "#5a4478",
        fontSize: "16px",
        fontWeight: "bold",
    },
    switchSection: {
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        marginTop: "25px",
        gap: "10px",
        fontSize: "14px",
        color: "#5a4478",
    },
    switch: {
        position: "relative",
        display: "inline-block",
        width: "50px",
        height: "24px",
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
        transition: ".4s",
    },
    navbar: {
        display: "flex",
        justifyContent: "space-around",
        width: "100%",
        position: "fixed",
        bottom: "0",
        backgroundColor: "#f8f3fb",
        padding: "10px 0",
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
    activeNavButton: {
        borderBottom: "2px solid #5a4478",
        paddingBottom: "4px",
    },
};

export default AdminPage;
