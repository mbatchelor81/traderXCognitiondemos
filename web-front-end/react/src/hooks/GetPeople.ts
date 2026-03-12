import { SetStateAction, useEffect, useState } from "react";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';

export const GetPeople = () => {
	const [people, setPeople] = useState<JSON[]>([]);
	type data = () => Promise<unknown>;
  useEffect(() => {
		let json:SetStateAction<JSON[]>;
    const loadPeople:data = async () => {
			try {
				const response = await fetchWithTenant(`${Environment.people_service_url}/people/`);
				if (response.ok) {
					json = await response.json();
					setPeople(json);
				}
			} catch (error) {
				return error;
			}
    }
    loadPeople();
  }, []);
	return people;
}
