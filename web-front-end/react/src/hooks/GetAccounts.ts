import { useEffect, useState } from "react";
import { AccountData } from "../AccountsDropdown";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';

export const GetAccounts = () => {
	const [accounts, setAccounts] = useState<AccountData[]>([]);
  useEffect(() => {
    const loadAccounts = async () => {
      const response = await fetchWithTenant(`${Environment.account_service_url}/account/`);
      if (response.ok) {
        const accounts = await response.json();
        setAccounts(accounts);
      }
      else {
        console.log('error');
      }
    }
    loadAccounts();
  }, []);
	return accounts
}
