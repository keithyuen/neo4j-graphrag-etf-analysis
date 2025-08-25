import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Graph from '../Graph';

// Mock the CytoscapeGraph component
vi.mock('../../components/graph/CytoscapeGraph', () => ({
  default: () => (
    <div data-testid="cytoscape-graph">
      <div>Mocked Cytoscape Graph Component</div>
    </div>
  )
}));

const GraphWithRouter = () => (
  <BrowserRouter>
    <Graph />
  </BrowserRouter>
);

describe('Graph', () => {
  it('renders page title and description', () => {
    render(<GraphWithRouter />);
    
    expect(screen.getByText(/interactive etf graph/i)).toBeInTheDocument();
    expect(screen.getByText(/explore etf holdings/i)).toBeInTheDocument();
  });

  it('renders the CytoscapeGraph component', () => {
    render(<GraphWithRouter />);
    
    expect(screen.getByTestId('cytoscape-graph')).toBeInTheDocument();
    expect(screen.getByText('Mocked Cytoscape Graph Component')).toBeInTheDocument();
  });

  it('provides link back to home page', () => {
    render(<GraphWithRouter />);
    
    const homeLink = screen.getByText(/back to queries/i);
    expect(homeLink).toBeInTheDocument();
    expect(homeLink.closest('a')).toHaveAttribute('href', '/');
  });

  it('shows graph usage instructions', () => {
    render(<GraphWithRouter />);
    
    expect(screen.getByText(/how to use/i)).toBeInTheDocument();
    expect(screen.getByText(/select an etf/i)).toBeInTheDocument();
    expect(screen.getByText(/adjust the number/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a layout/i)).toBeInTheDocument();
  });

  it('displays graph features information', () => {
    render(<GraphWithRouter />);
    
    expect(screen.getByText(/features/i)).toBeInTheDocument();
    expect(screen.getByText(/interactive visualization/i)).toBeInTheDocument();
    expect(screen.getByText(/multiple layout algorithms/i)).toBeInTheDocument();
    expect(screen.getByText(/hover tooltips/i)).toBeInTheDocument();
  });

  it('has proper layout structure', () => {
    render(<GraphWithRouter />);
    
    // Should have a main container
    const mainContainer = screen.getByRole('main');
    expect(mainContainer).toBeInTheDocument();
    
    // Should have header section
    expect(screen.getByText(/interactive etf graph/i)).toBeInTheDocument();
    
    // Should have graph section
    expect(screen.getByTestId('cytoscape-graph')).toBeInTheDocument();
  });

  it('maintains responsive design elements', () => {
    render(<GraphWithRouter />);
    
    // Check for responsive classes (assuming Tailwind CSS)
    const container = screen.getByRole('main');
    expect(container).toHaveClass('container', 'mx-auto', 'px-4');
  });

  it('includes accessibility features', () => {
    render(<GraphWithRouter />);
    
    // Should have proper heading hierarchy
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toHaveTextContent(/interactive etf graph/i);
    
    // Should have proper navigation links
    const homeLink = screen.getByRole('link', { name: /back to queries/i });
    expect(homeLink).toBeInTheDocument();
  });

  it('handles component mounting and unmounting', () => {
    const { unmount } = render(<GraphWithRouter />);
    
    expect(screen.getByTestId('cytoscape-graph')).toBeInTheDocument();
    
    // Should unmount without errors
    unmount();
  });
});