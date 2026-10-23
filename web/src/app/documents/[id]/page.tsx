"use client";

import { useParams } from "next/navigation";

import { DocumentScreen } from "@/components/DocumentScreen";

export default function DocumentPage() {
  const params = useParams<{ id: string }>();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  if (!id) return null;
  return <DocumentScreen id={id} />;
}
