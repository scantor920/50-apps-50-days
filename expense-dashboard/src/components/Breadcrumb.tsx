import { Link } from 'react-router-dom';

interface BreadcrumbProps {
  crumbs: { label: string; href?: string }[];
}

export function Breadcrumb({ crumbs }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" style={{ marginBottom: 16, color: 'var(--ink-3)', fontSize: 13 }}>
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`}>
            {crumb.href && !isLast ? <Link to={crumb.href}>{crumb.label}</Link> : crumb.label}
                {!isLast ? ' › ' : ''}
          </span>
        );
      })}
    </nav>
  );
}
