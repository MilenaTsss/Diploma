import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const VerificationPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [phone, setPhone] = useState(() => location.state?.phone || "+79888363930");
    const [isEditing, setIsEditing] = useState(false);
    const [code, setCode] = useState("");
    const [timer, setTimer] = useState(30);
    const [isResendDisabled, setIsResendDisabled] = useState(true);

    useEffect(() => {
        if (timer > 0) {
            const interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
            return () => clearInterval(interval);
        } else {
            setIsResendDisabled(false);
        }
    }, [timer]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log("Код подтверждения:", code);
        navigate("/user"); // Перенаправление на страницу пользователя
    };

    const handleResendCode = () => {
        setTimer(30);
        setIsResendDisabled(true);
    };

    return (
        <div style={styles.container}>
            <h2 style={styles.title}>Мобильный телефон</h2>
            {isEditing ? (
                <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    style={styles.input}
                    maxLength={12}
                />
            ) : (
                <p style={styles.phoneNumber}>{phone}</p>
            )}
            <a href="#" style={styles.changeNumber} onClick={() => setIsEditing(!isEditing)}>
                {isEditing ? "Сохранить номер" : "Изменить номер телефона"}
            </a>
            <h3 style={styles.subtitle}>Код подтверждения</h3>
            <form onSubmit={handleSubmit} style={styles.form}>
                <label htmlFor="code" style={styles.label}>Код</label>
                <input
                    id="code"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    maxLength={6}
                    style={styles.input}
                    required
                />
                <p style={styles.helperText}>На телефон выслан код подтверждения</p>
                <button type="submit" style={styles.confirmButton}>Подтвердить</button>
            </form>
            <button
                style={isResendDisabled ? styles.resendButtonDisabled : styles.resendButton}
                onClick={handleResendCode}
                disabled={isResendDisabled}
            >
                Отправить код повторно
            </button>
            {isResendDisabled && (
                <div style={styles.timerBox}>
                    <span style={styles.timerText}>⏳ Отправить код повторно можно через {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, "0")}</span>
                </div>
            )}
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        width: "100vw",
        backgroundColor: "#fef7fb",
        padding: "20px",
    },
    title: {
        fontSize: "24px",
        fontWeight: "bold",
        color: "#5a4478",
    },
    phoneNumber: {
        fontSize: "18px",
        marginBottom: "5px",
    },
    changeNumber: {
        color: "#5a4478",
        textDecoration: "underline",
        cursor: "pointer",
        marginBottom: "10px",
    },
    subtitle: {
        fontSize: "20px",
        fontWeight: "bold",
        marginTop: "20px",
    },
    form: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%",
    },
    label: {
        fontSize: "14px",
        marginBottom: "5px",
    },
    input: {
        width: "280px",
        fontSize: "18px",
        padding: "12px",
        borderRadius: "8px",
        border: "1px solid #ccc",
        outline: "none",
        textAlign: "center",
    },
    helperText: {
        fontSize: "12px",
        color: "#666",
        marginTop: "5px",
    },
    confirmButton: {
        backgroundColor: "#5a4478",
        color: "#fff",
        border: "none",
        padding: "12px 20px",
        borderRadius: "25px",
        cursor: "pointer",
        fontSize: "16px",
        marginTop: "15px",
        width: "300px",
    },
    resendButton: {
        backgroundColor: "#d7c4ed",
        color: "#5a4478",
        border: "none",
        padding: "12px 20px",
        borderRadius: "25px",
        cursor: "pointer",
        fontSize: "16px",
        marginTop: "15px",
        width: "300px",
    },
    resendButtonDisabled: {
        backgroundColor: "#eae0f5",
        color: "#a89bb5",
        border: "none",
        padding: "12px 20px",
        borderRadius: "25px",
        fontSize: "16px",
        marginTop: "15px",
        width: "300px",
        cursor: "not-allowed",
    },
    timerBox: {
        marginTop: "10px",
        padding: "10px",
        border: "1px solid #ccc",
        borderRadius: "10px",
    },
    timerText: {
        fontSize: "14px",
        color: "#666",
    },
};

export default VerificationPage;
