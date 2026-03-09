// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Set REACT_APP_TENANT_ID for single-tenant mode in test environment
process.env.REACT_APP_TENANT_ID = 'test_tenant';
