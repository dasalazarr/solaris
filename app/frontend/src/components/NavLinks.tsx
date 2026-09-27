"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export interface NavItem {
  href: string;
  code: string;
  label: string;
}

/** Navegación principal. Solo recibe las pantallas que el rol (dicho por el backend) puede ver. */
export default function NavLinks({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  if (items.length === 0) {
    return (
      <nav className="tabs" aria-label="Pantallas">
        <span className="tabs-empty">Tu rol no tiene pantallas del flujo 8D en este demo.</span>
      </nav>
    );
  }
  return (
    <nav className="tabs" aria-label="Pantallas">
      {items.map((it) => {
        const active = pathname === it.href || pathname.startsWith(`${it.href}/`);
        return (
          <Link key={it.href} href={it.href} aria-current={active ? "page" : undefined}>
            <span className="code">{it.code}</span> {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
