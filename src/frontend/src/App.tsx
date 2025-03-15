import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginUserPage from "./pages/LoginUserPage";

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginUserPage />} />
            </Routes>
        </Router>
    );
};

export default App;
