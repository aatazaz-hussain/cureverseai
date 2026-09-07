import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL =
  process.env.CUREVERSEAI_BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(
      `${BACKEND_URL}/api/v1/analyze`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: "drug_development",
          ...body,
        }),
        cache: "no-store",
      }
    );

    const text = await response.text();

    let data: any;

    try {
      data = JSON.parse(text);
    } catch {
      return NextResponse.json(
        {
          error: "Backend returned a non-JSON response.",
          status: response.status,
          response: text.slice(0, 1000),
        },
        { status: 502 }
      );
    }

    return NextResponse.json(data, {
      status: response.status,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        error: "Drug development backend is unavailable.",
        message: error?.message || "Unknown error",
      },
      { status: 502 }
    );
  }
}
