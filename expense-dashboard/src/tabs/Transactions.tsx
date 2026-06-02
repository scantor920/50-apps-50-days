import { useMemo, useState } from 'react';
import { useReactTable, getCoreRowModel, flexRender, createColumnHelper } from '@tanstack/react-table';
import { Breadcrumb } from '../components/Breadcrumb';
import { KpiTile } from '../components/KpiTile';
import { QueryState } from '../components/QueryState';
import type { Transaction } from '../data/types';
import { useTransactions } from '../data/useTransactions';
import { formatCurrency } from '../lib/formatters';
import { useDrill } from '../lib/useDrill';

const columnHelper = createColumnHelper<Transaction>();

const columns = [
  columnHelper.accessor('date', { header: 'Date' }),
  columnHelper.accessor('id', { header: 'Txn ID' }),
  columnHelper.accessor('vendorName', { header: 'Vendor' }),
  columnHelper.accessor('memo', { header: 'Memo' }),
  columnHelper.accessor('glId', { header: 'GL' }),
  columnHelper.accessor('ccId', { header: 'Cost Center' }),
  columnHelper.accessor('invoiceNumber', { header: 'Invoice' }),
  columnHelper.accessor('status', { header: 'Status' }),
  columnHelper.accessor('amount', {
    header: 'Amount',
    cell: (ctx) => <span className="tabular-nums">{formatCurrency(ctx.getValue())}</span>,
  }),
];

export function TransactionsTab() {
  const period = useDrill((s) => s.period);
  const filter = useDrill((s) => s.filter);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<'All' | 'Posted' | 'Pending' | 'Reclassed' | 'Voided'>('All');

  const query = useTransactions(period, filter, page, 200);
  const rows = query.data?.rows ?? [];

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      const text = `${row.memo} ${row.vendorName} ${row.invoiceNumber}`.toLowerCase();
      const searchMatch = text.includes(search.toLowerCase());
      const statusMatch = status === 'All' ? true : row.status === status;
      return searchMatch && statusMatch;
    });
  }, [rows, search, status]);

  const posted = filteredRows.filter((row) => row.status === 'Posted').length;
  const pending = filteredRows.filter((row) => row.status === 'Pending').length;
  const reclassed = filteredRows.filter((row) => row.status === 'Reclassed').length;
  const totalAmount = filteredRows.reduce((sum, row) => sum + row.amount, 0);

  const table = useReactTable({
    data: filteredRows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <QueryState isLoading={query.isLoading} isError={query.isError} onRetry={() => void query.refetch()}>
      <div className="page">
        <Breadcrumb crumbs={[{ label: 'Overview', href: '/overview' }, { label: 'P&L', href: '/pnl' }, { label: 'Cost Centers', href: '/cost-centers' }, { label: 'Vendors', href: '/vendors' }, { label: 'Transactions' }]} />

        <div className="grid grid-4">
          <KpiTile eyebrow="Total $" value={formatCurrency(totalAmount)} deltaValue={0} deltaMode="budget" footnote="Filtered result" />
          <KpiTile eyebrow="Posted" value={String(posted)} deltaValue={0} deltaMode="prior" footnote="Count" />
          <KpiTile eyebrow="Pending" value={String(pending)} deltaValue={0} deltaMode="prior" footnote="Count" />
          <KpiTile eyebrow="Reclassed" value={String(reclassed)} deltaValue={0} deltaMode="prior" footnote="Count" />
        </div>

        <div className="panel" style={{ marginTop: 16, padding: 16 }}>
          <input
            placeholder="Search memo / vendor / invoice"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            style={{ width: 340 }}
          />

          <div style={{ display: 'inline-flex', marginLeft: 12 }}>
            {['All', 'Posted', 'Pending', 'Reclassed', 'Voided'].map((choice) => (
              <button key={choice} type="button" onClick={() => setStatus(choice as typeof status)}>{choice}</button>
            ))}
          </div>

          <div style={{ overflow: 'auto', maxHeight: 540, marginTop: 16 }}>
            <table style={{ width: '100%' }}>
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th key={header.id} align="left">
                        {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12 }}>
            <button type="button" disabled={page <= 1} onClick={() => setPage((prev) => prev - 1)}>Previous</button>
            <span>Page {page}</span>
            <button type="button" disabled={rows.length < 200} onClick={() => setPage((prev) => prev + 1)}>Next</button>
          </div>
        </div>
      </div>
    </QueryState>
  );
}
