import { render, screen } from '@testing-library/react';
import { VariancePill } from '../components/VariancePill';

describe('VariancePill', () => {
  test('shows up arrow and budget context for positive budget variance', () => {
    render(<VariancePill value={12.5} mode="budget" isPercent={false} />);
    expect(screen.getByLabelText('+ $12.5K versus budget')).toBeInTheDocument();
    expect(screen.getByText('▲')).toBeInTheDocument();
  });

  test('shows down arrow and prior year context for negative prior variance', () => {
    render(<VariancePill value={-3.2} mode="prior" isPercent={true} />);
    expect(screen.getByLabelText('- 3.2% versus prior year')).toBeInTheDocument();
    expect(screen.getByText('▼')).toBeInTheDocument();
  });
});
