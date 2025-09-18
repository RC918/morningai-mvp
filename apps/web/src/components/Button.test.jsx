import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './ui/button'; // 假設您的 Button 組件路徑
import { expect, test, vi } from 'vitest';

test('Button renders with correct text', () => {
  render(<Button>Click Me</Button>);
  expect(screen.getByText('Click Me')).toBeInTheDocument();
});

test('Button handles click events', async () => {
  const handleClick = vi.fn();
  render(<Button onClick={handleClick}>Clickable</Button>);
  await userEvent.click(screen.getByText('Clickable'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});


