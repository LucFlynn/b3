"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";
import { createApi } from "./api";

export function useApi() {
  const { getToken } = useAuth();

  const getApi = useCallback(async () => {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    return createApi(token);
  }, [getToken]);

  return { getApi };
}
