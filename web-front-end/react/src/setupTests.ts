// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// The tenant is a build-time constant; tests build against a fixed test tenant.
process.env.REACT_APP_TENANT_ID = process.env.REACT_APP_TENANT_ID || 'test_tenant';
