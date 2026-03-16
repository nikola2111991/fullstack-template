/**
 * useFetch: React hook for data fetching with loading/error/data states
 * Usage:
 *   const { data, error, loading, refetch } = useFetch<User[]>("/api/users");
 *   const { mutate, loading } = useMutation<User>("/api/users", { method: "POST" });
 */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface ApiResponse<T> {
    data: T | null;
    error: { code: string; message: string; status: number } | null;
}

interface UseFetchReturn<T> {
    data: T | null;
    error: { code: string; message: string; status: number } | null;
    loading: boolean;
    refetch: () => Promise<void>;
}

export function useFetch<T>(
    path: string | null,
    options?: RequestInit & { baseUrl?: string }
): UseFetchReturn<T> {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<ApiResponse<T>["error"]>(null);
    const [loading, setLoading] = useState(!!path);
    const abortRef = useRef<AbortController | null>(null);

    const fetchData = useCallback(async () => {
        if (!path) return;

        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;

        setLoading(true);
        setError(null);

        try {
            const { baseUrl = "", ...fetchOptions } = options ?? {};
            const response = await fetch(`${baseUrl}${path}`, {
                ...fetchOptions,
                signal: controller.signal,
                headers: { "Content-Type": "application/json", ...fetchOptions?.headers },
            });

            if (!response.ok) {
                const body = await response.json().catch(() => ({}));
                setError(body.error ?? { code: "HTTP_ERROR", message: response.statusText, status: response.status });
                setData(null);
                return;
            }

            const json: ApiResponse<T> = await response.json();
            setData(json.data);
            setError(json.error);
        } catch (err) {
            if (err instanceof DOMException && err.name === "AbortError") return;
            setError({ code: "NETWORK_ERROR", message: err instanceof Error ? err.message : "Unknown error", status: 0 });
            setData(null);
        } finally {
            setLoading(false);
        }
    }, [path, options]);

    useEffect(() => {
        fetchData();
        return () => abortRef.current?.abort();
    }, [fetchData]);

    return { data, error, loading, refetch: fetchData };
}

// ---- Mutation Hook ----

interface UseMutationReturn<T> {
    data: T | null;
    error: { code: string; message: string; status: number } | null;
    loading: boolean;
    mutate: (body?: unknown) => Promise<T | null>;
    reset: () => void;
}

export function useMutation<T>(
    path: string,
    options?: RequestInit & { baseUrl?: string }
): UseMutationReturn<T> {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<ApiResponse<T>["error"]>(null);
    const [loading, setLoading] = useState(false);

    const mutate = useCallback(async (body?: unknown): Promise<T | null> => {
        setLoading(true);
        setError(null);

        try {
            const { baseUrl = "", ...fetchOptions } = options ?? {};
            const response = await fetch(`${baseUrl}${path}`, {
                method: "POST",
                ...fetchOptions,
                headers: { "Content-Type": "application/json", ...fetchOptions?.headers },
                body: body ? JSON.stringify(body) : undefined,
            });

            const json: ApiResponse<T> = await response.json();
            if (!response.ok) {
                setError(json.error ?? { code: "HTTP_ERROR", message: response.statusText, status: response.status });
                setData(null);
                return null;
            }
            setData(json.data);
            return json.data;
        } catch (err) {
            setError({ code: "NETWORK_ERROR", message: err instanceof Error ? err.message : "Unknown error", status: 0 });
            return null;
        } finally {
            setLoading(false);
        }
    }, [path, options]);

    const reset = useCallback(() => {
        setData(null);
        setError(null);
        setLoading(false);
    }, []);

    return { data, error, loading, mutate, reset };
}
