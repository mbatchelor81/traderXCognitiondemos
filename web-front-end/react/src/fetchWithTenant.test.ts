import { fetchWithTenant, setCurrentTenant, getCurrentTenant } from './fetchWithTenant';

describe('fetchWithTenant', () => {
  beforeEach(() => {
    setCurrentTenant('acme_corp');
    global.fetch = jest.fn().mockResolvedValue(new Response());
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('getCurrentTenant returns the current tenant', () => {
    expect(getCurrentTenant()).toBe('acme_corp');
  });

  test('setCurrentTenant updates the current tenant', () => {
    setCurrentTenant('globex_inc');
    expect(getCurrentTenant()).toBe('globex_inc');
  });

  test('injects X-Tenant-ID header into fetch requests', async () => {
    await fetchWithTenant('http://localhost:8000/api/test');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/test',
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );
    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const headers = callArgs[1].headers as Headers;
    expect(headers.get('X-Tenant-ID')).toBe('acme_corp');
  });

  test('uses the updated tenant in subsequent requests', async () => {
    setCurrentTenant('initech');
    await fetchWithTenant('http://localhost:8000/api/test');
    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const headers = callArgs[1].headers as Headers;
    expect(headers.get('X-Tenant-ID')).toBe('initech');
  });

  test('preserves existing headers from init', async () => {
    await fetchWithTenant('http://localhost:8000/api/test', {
      headers: { 'Content-Type': 'application/json' },
    });
    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const headers = callArgs[1].headers as Headers;
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('X-Tenant-ID')).toBe('acme_corp');
  });

  test('passes through other fetch init options', async () => {
    await fetchWithTenant('http://localhost:8000/api/test', {
      method: 'POST',
      body: JSON.stringify({ data: 'test' }),
    });
    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    expect(callArgs[1].method).toBe('POST');
    expect(callArgs[1].body).toBe(JSON.stringify({ data: 'test' }));
  });
});
