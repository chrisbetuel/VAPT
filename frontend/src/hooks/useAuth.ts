import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { LoginRequest, RegisterRequest } from "@/types";

export function useLogin() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data.email, data.password),
    onSuccess: (response) => {
      const { user, ...tokens } = response.data;
      setAuth(user, tokens);
      navigate("/dashboard");
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (response) => {
      const { user, ...tokens } = response.data;
      setAuth(user, tokens);
      navigate("/dashboard");
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  return () => {
    logout();
    navigate("/login");
  };
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["current-user"],
    queryFn: () => authApi.me(),
    retry: false,
  });
}
