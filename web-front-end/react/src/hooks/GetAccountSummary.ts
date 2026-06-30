import { useEffect, useState } from "react";
import { AccountSummary } from "../Datatable/types";
import { Environment } from "../env";
import { fetchWithTenant } from "../fetchWithTenant";
import { useTenant } from "../TenantContext";

export const GetAccountSummary = (
        accountId: number,
        refreshTrigger?: number,
) => {
        const { tenant } = useTenant();
        const [summaryData, setSummaryData] = useState<AccountSummary | null>(null);

        // Clear stale data immediately when the account or tenant changes so the
        // cards never show the previous account's numbers during the refetch.
        useEffect(() => {
                setSummaryData(null);
        }, [accountId, tenant]);

        useEffect(() => {
                if (accountId === 0) {
                        return;
                }

                const abortController = new AbortController();

                const fetchData = async () => {
                        try {
                                const response = await fetchWithTenant(
                                        `${Environment.account_service_url}/account/${accountId}/summary`,
                                        { signal: abortController.signal }
                                );

                                if (response.ok) {
                                        const json = await response.json();
                                        if (!abortController.signal.aborted) {
                                                setSummaryData(json);
                                        }
                                } else if (!abortController.signal.aborted) {
                                        setSummaryData(null);
                                }
                        } catch (error) {
                                if (error instanceof DOMException && error.name === "AbortError") {
                                        return;
                                }
                                if (!abortController.signal.aborted) {
                                        setSummaryData(null);
                                }
                        }
                };

                fetchData();
                return () => {
                        abortController.abort();
                };
        }, [accountId, tenant, refreshTrigger]);

        return summaryData;
};
